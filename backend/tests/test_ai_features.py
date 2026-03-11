"""
Backend Tests for NT Commerce AI Features
Tests AI Chat, Agents Status, and Financial Health endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIFeatures:
    """Test AI-related API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login first to get auth token
        self._login()
        
    def _login(self):
        """Login as tenant user and get token"""
        login_payload = {
            "email": "ncr@ntcommerce.com",
            "password": "Test@123"
        }
        response = self.session.post(f"{BASE_URL}/api/auth/unified-login", json=login_payload)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                print(f"Successfully logged in, token obtained")
                return True
        print(f"Login failed: {response.status_code} - {response.text}")
        return False

    # ============ AI AGENTS STATUS TESTS ============
    
    def test_ai_agents_status_endpoint(self):
        """Test GET /api/ai/agents/status returns list of 8 agents"""
        response = self.session.get(f"{BASE_URL}/api/ai/agents/status")
        
        print(f"Agents Status Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Agents data: {data}")
        
        # Should be a list of 8 agents
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 8, f"Expected 8 agents, got {len(data)}"
        
        # Verify each agent has required fields
        expected_agents = [
            "invoice_processor",
            "expense_classifier", 
            "financial_analyzer",
            "fraud_detector",
            "smart_reporter",
            "tax_assistant",
            "forecaster",
            "daily_automation"
        ]
        
        agent_ids = [agent.get("id") for agent in data]
        for expected_id in expected_agents:
            assert expected_id in agent_ids, f"Missing agent: {expected_id}"
        
        # Verify agent structure
        for agent in data:
            assert "id" in agent, "Agent should have 'id' field"
            assert "is_enabled" in agent, "Agent should have 'is_enabled' field"
            assert "name" in agent or "name_en" in agent, "Agent should have name"
            print(f"Agent: {agent.get('id')} - Enabled: {agent.get('is_enabled')}")

    # ============ FINANCIAL HEALTH TESTS ============
    
    def test_financial_health_endpoint(self):
        """Test GET /api/ai/financial-health returns health data"""
        response = self.session.get(f"{BASE_URL}/api/ai/financial-health")
        
        print(f"Financial Health Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Financial Health data: {data}")
        
        # Verify required fields
        assert "overall_score" in data, "Should have overall_score"
        assert "monthly_revenue" in data, "Should have monthly_revenue"
        assert "monthly_expenses" in data, "Should have monthly_expenses"
        assert "net_income" in data, "Should have net_income"
        assert "cash_balance" in data, "Should have cash_balance"
        
        # Score should be between 0 and 100
        score = data.get("overall_score", 0)
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
        
        # Health indicators should be present
        assert "health_indicators" in data, "Should have health_indicators"
        
        print(f"Financial Health Score: {score}")
        print(f"Monthly Revenue: {data.get('monthly_revenue')}")
        print(f"Monthly Expenses: {data.get('monthly_expenses')}")
        print(f"Net Income: {data.get('net_income')}")

    # ============ AI CHAT TESTS ============
    
    def test_ai_chat_endpoint(self):
        """Test POST /api/ai/chat accepts message and returns AI response"""
        chat_payload = {
            "message": "ما هي أرباح هذا الشهر؟",
            "session_id": ""
        }
        
        response = self.session.post(f"{BASE_URL}/api/ai/chat", json=chat_payload)
        
        print(f"AI Chat Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"AI Chat data: {data}")
        
        # Verify required fields
        assert "session_id" in data, "Should have session_id"
        assert "response" in data, "Should have response"
        
        # Response should not be empty
        ai_response = data.get("response", "")
        assert len(ai_response) > 0, "AI response should not be empty"
        
        print(f"AI Response: {ai_response[:200]}...")
        
        # Session ID should be generated
        session_id = data.get("session_id")
        assert session_id and len(session_id) > 0, "Session ID should be generated"
        print(f"Session ID: {session_id}")

    def test_ai_chat_sessions_endpoint(self):
        """Test GET /api/ai/chat/sessions returns user sessions"""
        response = self.session.get(f"{BASE_URL}/api/ai/chat/sessions")
        
        print(f"Chat Sessions Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Chat Sessions data: {data}")
        
        # Should be a list
        assert isinstance(data, list), "Response should be a list"
        
        print(f"Number of chat sessions: {len(data)}")

    # ============ AI INSIGHTS TESTS ============
    
    def test_ai_insights_endpoint(self):
        """Test GET /api/ai/insights returns insights and alerts"""
        response = self.session.get(f"{BASE_URL}/api/ai/insights")
        
        print(f"AI Insights Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"AI Insights data: {data}")
        
        # Verify structure
        assert "insights" in data, "Should have insights"
        assert "alerts" in data or "financial_health" in data, "Should have alerts or financial_health"
        
        print(f"Number of insights: {len(data.get('insights', []))}")
        print(f"Number of alerts: {len(data.get('alerts', []))}")

    # ============ FORECAST TESTS ============
    
    def test_forecast_revenue_endpoint(self):
        """Test GET /api/ai/forecast/revenue returns forecast data"""
        response = self.session.get(f"{BASE_URL}/api/ai/forecast/revenue?periods=3")
        
        print(f"Forecast Revenue Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Forecast data: {data}")
        
        # Verify required fields
        assert "forecast_type" in data or "trend" in data, "Should have forecast_type or trend"

    # ============ DAILY SUMMARY TESTS ============
    
    def test_daily_summary_endpoint(self):
        """Test GET /api/ai/daily-summary returns daily summary"""
        response = self.session.get(f"{BASE_URL}/api/ai/daily-summary")
        
        print(f"Daily Summary Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Daily Summary data: {data}")

    # ============ RUN AGENT TESTS ============
    
    def test_run_expense_classifier_agent(self):
        """Test POST /api/ai/agents/run with expense classifier"""
        payload = {
            "agent_type": "expense_classifier",
            "task_data": {
                "description": "فاتورة الكهرباء",
                "amount": 5000,
                "vendor": "شركة الكهرباء"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/ai/agents/run", json=payload)
        
        print(f"Run Agent Response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Agent Result: {data}")
        
        # Should have success flag
        assert "success" in data, "Should have success flag"
        
        if data.get("success"):
            print("Agent executed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
