
from fastapi.testclient import TestClient
from api_mocker.dashboard import DashboardManager
from unittest.mock import MagicMock
import pytest

class MockAnalytics:
    def get_server_metrics(self):
        # Return object with attributes as expected by dashboard
        from dataclasses import dataclass
        @dataclass
        class Metrics:
            uptime_seconds: float = 100
            total_requests: int = 50
            requests_per_minute: float = 1.0
            average_response_time_ms: float = 20.0
            error_rate: float = 0.0
            memory_usage_mb: float = 50.0
            cpu_usage_percent: float = 1.0
            
        return Metrics()

    def get_analytics_summary(self, hours):
        return {
            "methods": {"GET": 10},
            "status_codes": {"200": 10},
            "popular_endpoints": {"/api/test": 5},
            "slowest_endpoints": {"/api/slow": 100}
        }

@pytest.fixture
def dashboard_client():
    mock_analytics = MockAnalytics()
    dashboard = DashboardManager(analytics_manager=mock_analytics)
    return TestClient(dashboard.app)

def test_dashboard_home(dashboard_client):
    response = dashboard_client.get("/")
    assert response.status_code == 200
    assert "API-Mocker Dashboard" in response.text
    assert "<!DOCTYPE html>" in response.text

def test_api_metrics(dashboard_client):
    response = dashboard_client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 50

def test_api_analytics(dashboard_client):
    response = dashboard_client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "popular_endpoints" in data

def test_api_endpoints(dashboard_client):
    response = dashboard_client.get("/api/endpoints")
    assert response.status_code == 200
    data = response.json()
    assert "/api/test" in data["popular_endpoints"]
