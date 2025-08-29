from fastapi import FastAPI, WebSocket, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import asyncio
import json
import time
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Import our new modules
import sys
import os

# Add the root directory to the path for imports
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, root_dir)

from packages.api.core.auth.auth_manager import AuthManager, APIKeyManager
from packages.api.core.billing.billing_manager import BillingManager, PaymentProcessor
from packages.api.core.products.ai_services import PRODUCTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NEURA")

app = FastAPI(
    title="NEURA AI SaaS Factory",
    description="Automated AI SaaS services with API key monetization",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (check if directory exists first)
ui_directory = os.path.join(root_dir, "packages", "ui")
if os.path.exists(ui_directory):
    app.mount("/ui", StaticFiles(directory=ui_directory), name="ui")

# Initialize managers
auth_manager = AuthManager()
billing_manager = BillingManager()
payment_processor = PaymentProcessor()

# WebSocket connections store
connections: Dict[str, WebSocket] = {}

# Serve dashboard at root
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the SaaS dashboard"""
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "saas-dashboard", "index.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

# Pydantic models
class UserRegistration(BaseModel):
    email: str
    password: str

class SubscriptionRequest(BaseModel):
    plan_id: str
    payment_method_id: str

class PaymentRequest(BaseModel):
    service_id: str
    payment_method_id: str

class ResumeReviewRequest(BaseModel):
    resume_text: str
    job_description: Optional[str] = None

class LandingPageRequest(BaseModel):
    name: str
    industry: str
    target_audience: str
    benefits: List[str]

class NameGeneratorRequest(BaseModel):
    industry: str
    keywords: List[str]
    style: str = "modern"

class SEOAuditRequest(BaseModel):
    url: str

class LogoRequest(BaseModel):
    company_name: str
    industry: str
    style: str = "modern"

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections[client_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            await broadcast_message(f"Client {client_id}: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        del connections[client_id]

async def broadcast_message(message: str):
    """Broadcast message to all connected clients"""
    for connection in connections.values():
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "name": "NEURA AI SaaS Factory",
        "version": "2.0.0",
        "status": "operational",
        "services": list(PRODUCTS.keys()),
        "pricing_plans": list(billing_manager.plans.keys()),
        "timestamp": datetime.now().isoformat()
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "ai_services": "operational",
            "billing": "active"
        },
        "timestamp": datetime.now().isoformat()
    }


# Authentication endpoints
@app.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user and get API key"""
    try:
        result = auth_manager.create_user(user_data.email, user_data.password)
        return {
            "message": "User registered successfully",
            "user_id": result["user_id"],
            "api_key": result["api_key"],
            "email": result["email"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/api-key")
async def generate_api_key(
    name: str = "Default",
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """Generate a new API key for authenticated user"""
    api_key_info = auth_manager.api_key_manager.generate_api_key(
        current_user["user_id"], name
    )
    return api_key_info

# Billing endpoints
@app.get("/billing/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    return {"plans": billing_manager.plans}

@app.post("/billing/subscribe")
async def create_subscription(
    subscription_data: SubscriptionRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """Create a new subscription"""
    result = await billing_manager.create_subscription(
        current_user["user_id"],
        subscription_data.plan_id,
        subscription_data.payment_method_id
    )
    return result

@app.get("/billing/subscription")
async def get_subscription(current_user: dict = Depends(auth_manager.get_current_user)):
    """Get current subscription details"""
    subscription = billing_manager.get_user_subscription(current_user["user_id"])
    if not subscription:
        return {"message": "No active subscription"}
    return subscription

@app.get("/billing/usage")
async def get_usage_stats(current_user: dict = Depends(auth_manager.get_current_user)):
    """Get usage statistics"""
    usage_limits = billing_manager.check_usage_limits(current_user["user_id"])
    usage_stats = auth_manager.api_key_manager.get_user_usage(current_user["user_id"])
    return {**usage_limits, **usage_stats}

# AI Service endpoints
@app.post("/api/resume/review")
async def review_resume(
    request_data: ResumeReviewRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """AI Resume Review Service"""
    service = PRODUCTS["resume_reviewer"]
    result = await service.review_resume(
        request_data.resume_text,
        request_data.job_description
    )
    return result

@app.post("/api/landing-page/generate")
async def generate_landing_page(
    request_data: LandingPageRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """AI Landing Page Generator"""
    service = PRODUCTS["landing_page_generator"]
    business_info = {
        "name": request_data.name,
        "industry": request_data.industry,
        "target_audience": request_data.target_audience,
        "benefits": request_data.benefits
    }
    result = await service.generate_landing_page(business_info)
    return result

@app.post("/api/names/generate")
async def generate_names(
    request_data: NameGeneratorRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """AI Name/Brand Generator"""
    service = PRODUCTS["name_brand_generator"]
    result = await service.generate_names(
        request_data.industry,
        request_data.keywords,
        request_data.style
    )
    return result

@app.post("/api/seo/audit")
async def audit_website(
    request_data: SEOAuditRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """AI SEO Audit Bot"""
    service = PRODUCTS["seo_audit_bot"]
    result = await service.audit_website(request_data.url)
    return result

@app.post("/api/logo/generate")
async def generate_logo(
    request_data: LogoRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """AI Logo Maker"""
    service = PRODUCTS["logo_maker"]
    result = await service.generate_logo(
        request_data.company_name,
        request_data.industry,
        request_data.style
    )
    return result

# Analytics endpoints
@app.get("/analytics/dashboard")
async def get_analytics(current_user: dict = Depends(auth_manager.get_current_user)):
    """Get user analytics dashboard data"""
    usage_stats = auth_manager.api_key_manager.get_user_usage(current_user["user_id"])
    subscription = billing_manager.get_user_subscription(current_user["user_id"])
    billing_history = billing_manager.get_billing_history(current_user["user_id"])
    
    return {
        "usage": usage_stats,
        "subscription": subscription,
        "billing_history": billing_history,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
