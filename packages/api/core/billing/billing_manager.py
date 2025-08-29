
import stripe
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException
import os

# Set Stripe API key (use environment variable in production)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

class BillingManager:
    """Handle subscriptions, payments, and billing"""
    
    def __init__(self, db_path: str = "neura_saas.db"):
        self.db_path = db_path
        self.init_billing_tables()
        
        # Pricing plans
        self.plans = {
            "free": {
                "name": "Free",
                "price": 0,
                "requests_per_month": 100,
                "features": ["Basic API access", "Email support"]
            },
            "starter": {
                "name": "Starter",
                "price": 29.99,
                "requests_per_month": 5000,
                "features": ["All AI services", "Priority support", "API documentation"]
            },
            "professional": {
                "name": "Professional", 
                "price": 99.99,
                "requests_per_month": 25000,
                "features": ["All AI services", "24/7 support", "Custom integrations", "Analytics dashboard"]
            },
            "enterprise": {
                "name": "Enterprise",
                "price": 299.99,
                "requests_per_month": 100000,
                "features": ["All AI services", "Dedicated support", "Custom solutions", "SLA guarantee"]
            }
        }
    
    def init_billing_tables(self):
        """Initialize billing-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_id TEXT NOT NULL,
                stripe_subscription_id TEXT,
                status TEXT DEFAULT 'active',
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscription_id INTEGER,
                stripe_payment_id TEXT,
                amount REAL,
                currency TEXT DEFAULT 'usd',
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id)
            )
        ''')
        
        # Usage tracking for billing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                month TEXT,
                requests_count INTEGER DEFAULT 0,
                overage_charges REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def create_subscription(self, user_id: int, plan_id: str, payment_method_id: str) -> Dict:
        """Create a new subscription for a user"""
        
        if plan_id not in self.plans:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        plan = self.plans[plan_id]
        
        try:
            # Create Stripe customer
            customer = stripe.Customer.create(
                payment_method=payment_method_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Create Stripe subscription (skip for free plan)
            if plan_id != "free":
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': plan['name']},
                        'unit_amount': int(plan['price'] * 100),
                        'recurring': {'interval': 'month'}
                    }}],
                    expand=['latest_invoice.payment_intent']
                )
                stripe_sub_id = subscription.id
            else:
                stripe_sub_id = None
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO subscriptions (user_id, plan_id, stripe_subscription_id, current_period_start, current_period_end)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, 
                plan_id, 
                stripe_sub_id,
                datetime.now(),
                datetime.now() + timedelta(days=30)
            ))
            
            subscription_id = cursor.lastrowid
            
            # Update user plan
            cursor.execute('UPDATE users SET plan = ? WHERE id = ?', (plan_id, user_id))
            
            conn.commit()
            conn.close()
            
            return {
                "subscription_id": subscription_id,
                "plan": plan,
                "status": "active",
                "next_billing_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
    
    def get_user_subscription(self, user_id: int) -> Optional[Dict]:
        """Get current subscription for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, u.email 
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.user_id = ? AND s.status = 'active'
            ORDER BY s.created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            plan_id = result[2]
            return {
                "subscription_id": result[0],
                "plan_id": plan_id,
                "plan_details": self.plans.get(plan_id, {}),
                "status": result[4],
                "current_period_end": result[6],
                "email": result[7]
            }
        return None
    
    def check_usage_limits(self, user_id: int) -> Dict:
        """Check if user has exceeded usage limits"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return {"allowed": False, "reason": "No active subscription"}
        
        plan_id = subscription["plan_id"]
        plan = self.plans.get(plan_id, {})
        monthly_limit = plan.get("requests_per_month", 0)
        
        # Get current month usage
        current_month = datetime.now().strftime("%Y-%m")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT requests_count FROM monthly_usage 
            WHERE user_id = ? AND month = ?
        ''', (user_id, current_month))
        
        result = cursor.fetchone()
        current_usage = result[0] if result else 0
        
        conn.close()
        
        return {
            "allowed": current_usage < monthly_limit,
            "current_usage": current_usage,
            "monthly_limit": monthly_limit,
            "remaining": max(0, monthly_limit - current_usage),
            "plan": plan_id
        }
    
    def increment_usage(self, user_id: int):
        """Increment usage count for a user"""
        current_month = datetime.now().strftime("%Y-%m")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or update monthly usage
        cursor.execute('''
            INSERT INTO monthly_usage (user_id, month, requests_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, month) DO UPDATE SET
            requests_count = requests_count + 1
        ''', (user_id, current_month))
        
        conn.commit()
        conn.close()
    
    async def cancel_subscription(self, user_id: int) -> Dict:
        """Cancel a user's subscription"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Cancel in Stripe
        if subscription["plan_id"] != "free":
            try:
                stripe.Subscription.delete(subscription["subscription_id"])
            except stripe.error.StripeError as e:
                raise HTTPException(status_code=400, detail=f"Cancellation failed: {str(e)}")
        
        # Update in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions SET status = 'cancelled' 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        # Downgrade to free plan
        cursor.execute('UPDATE users SET plan = ? WHERE id = ?', ("free", user_id))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "cancelled",
            "message": "Subscription cancelled successfully",
            "new_plan": "free"
        }
    
    def get_billing_history(self, user_id: int) -> List[Dict]:
        """Get billing history for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, currency, status, created_at
            FROM payments
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "amount": result[0],
                "currency": result[1],
                "status": result[2],
                "date": result[3]
            }
            for result in results
        ]

class PaymentProcessor:
    """Handle one-time payments for individual services"""
    
    def __init__(self):
        self.service_prices = {
            "resume_review_basic": 9.99,
            "resume_review_detailed": 19.99,
            "resume_review_optimization": 29.99,
            "landing_page_basic": 29.99,
            "landing_page_premium": 49.99,
            "landing_page_complete": 99.99,
            "name_brand_package": 19.99,
            "brand_package": 39.99,
            "complete_identity": 79.99,
            "seo_audit_basic": 29.99,
            "seo_audit_comprehensive": 59.99,
            "seo_audit_monthly": 99.99,
            "logo_basic": 39.99,
            "logo_premium": 79.99,
            "logo_brand_identity": 149.99
        }
    
    async def process_payment(self, user_id: int, service_id: str, payment_method_id: str) -> Dict:
        """Process a one-time payment for a service"""
        
        if service_id not in self.service_prices:
            raise HTTPException(status_code=400, detail="Invalid service")
        
        amount = self.service_prices[service_id]
        
        try:
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True
            )
            
            # Save payment record
            conn = sqlite3.connect("neura_saas.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payments (user_id, stripe_payment_id, amount, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, payment_intent.id, amount, payment_intent.status))
            
            conn.commit()
            conn.close()
            
            return {
                "payment_id": payment_intent.id,
                "amount": amount,
                "status": payment_intent.status,
                "service": service_id
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
