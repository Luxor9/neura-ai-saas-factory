"""
Test configuration and fixtures for NEURA AI SaaS Factory
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add packages to path for testing
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        "JWT_SECRET": "test-secret",
        "STRIPE_SECRET_KEY": "sk_test_fake_key",
        "OPENAI_API_KEY": "sk-fake-openai-key",
        "DATABASE_URL": "sqlite:///:memory:",
        "ENVIRONMENT": "test"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def api_client():
    """Create a test client for the API"""
    try:
        from packages.api.core.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    except ImportError:
        pytest.skip("API package not available for testing")

@pytest.fixture
def mock_stripe():
    """Mock Stripe API for testing"""
    with patch('stripe.Customer') as mock_customer, \
         patch('stripe.Subscription') as mock_subscription, \
         patch('stripe.PaymentMethod') as mock_payment:
        
        # Mock successful responses
        mock_customer.create.return_value = Mock(id="cus_test123")
        mock_subscription.create.return_value = Mock(
            id="sub_test123",
            status="active",
            current_period_start=1234567890,
            current_period_end=1234567890 + 86400 * 30
        )
        mock_payment.attach.return_value = Mock(id="pm_test123")
        
        yield {
            "customer": mock_customer,
            "subscription": mock_subscription,
            "payment": mock_payment
        }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "test_password_123",
        "name": "Test User"
    }

@pytest.fixture
def sample_api_key():
    """Sample API key for testing"""
    return "neura_test_api_key_12345678901234567890123456789012"

# Test markers
pytest.register_assert_rewrite("tests.helpers")

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )