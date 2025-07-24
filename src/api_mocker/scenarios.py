"""
Scenario-Based Mocking System

Provides advanced scenario management for API mocking including:
- Multiple scenarios (happy path, error states, edge cases)
- Scenario switching via headers or query params
- Conditional responses based on request data
- A/B testing support for different response patterns
"""

import json
import random
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from enum import Enum


class ScenarioType(Enum):
    HAPPY_PATH = "happy_path"
    ERROR_SCENARIO = "error_scenario"
    EDGE_CASE = "edge_case"
    PERFORMANCE_TEST = "performance_test"
    A_B_TEST = "a_b_test"


@dataclass
class ScenarioCondition:
    """Defines conditions for when a scenario should be active."""
    header_match: Optional[Dict[str, str]] = None
    query_param_match: Optional[Dict[str, str]] = None
    body_match: Optional[Dict[str, Any]] = None
    path_match: Optional[str] = None
    method_match: Optional[str] = None
    probability: float = 1.0  # For A/B testing
    time_window: Optional[Dict[str, str]] = None  # Start/end times
    
    def matches(self, headers: Dict, query_params: Dict, body: Any, path: str, method: str) -> bool:
        """Check if the condition matches the current request."""
        # Check probability for A/B testing
        if random.random() > self.probability:
            return False
        
        # Check time window
        if self.time_window:
            now = datetime.now()
            start_time = datetime.fromisoformat(self.time_window.get('start', '00:00'))
            end_time = datetime.fromisoformat(self.time_window.get('end', '23:59'))
            current_time = now.replace(year=1900, month=1, day=1)
            if not (start_time <= current_time <= end_time):
                return False
        
        # Check headers
        if self.header_match:
            for key, value in self.header_match.items():
                if headers.get(key) != value:
                    return False
        
        # Check query parameters
        if self.query_param_match:
            for key, value in self.query_param_match.items():
                if query_params.get(key) != value:
                    return False
        
        # Check body
        if self.body_match and body:
            for key, value in self.body_match.items():
                if isinstance(body, dict) and body.get(key) != value:
                    return False
        
        # Check path
        if self.path_match:
            if not re.search(self.path_match, path):
                return False
        
        # Check method
        if self.method_match and method.upper() != self.method_match.upper():
            return False
        
        return True


@dataclass
class ScenarioResponse:
    """Defines a response for a specific scenario."""
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Union[Dict, List, str, Callable] = None
    delay: float = 0
    error_message: Optional[str] = None
    dynamic: bool = False


@dataclass
class Scenario:
    """Represents a complete scenario configuration."""
    name: str
    description: str
    scenario_type: ScenarioType
    condition: ScenarioCondition
    responses: Dict[str, ScenarioResponse]  # path -> response mapping
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class ScenarioManager:
    """Manages multiple scenarios and scenario switching."""
    
    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.active_scenario: Optional[str] = None
        self.default_scenario: str = "happy_path"
        self.scenario_history: List[Dict] = []
    
    def add_scenario(self, scenario: Scenario):
        """Add a new scenario to the manager."""
        self.scenarios[scenario.name] = scenario
        if scenario.name == "happy_path" and not self.default_scenario:
            self.default_scenario = scenario.name
    
    def get_scenario(self, name: str) -> Optional[Scenario]:
        """Get a scenario by name."""
        return self.scenarios.get(name)
    
    def list_scenarios(self) -> List[str]:
        """List all available scenarios."""
        return list(self.scenarios.keys())
    
    def activate_scenario(self, name: str) -> bool:
        """Activate a specific scenario."""
        if name in self.scenarios:
            self.active_scenario = name
            self._log_scenario_activation(name)
            return True
        return False
    
    def deactivate_scenario(self):
        """Deactivate the current scenario and return to default."""
        if self.active_scenario:
            self._log_scenario_deactivation(self.active_scenario)
        self.active_scenario = None
    
    def get_matching_scenario(self, headers: Dict, query_params: Dict, body: Any, path: str, method: str) -> Optional[Scenario]:
        """Find the best matching scenario for the current request."""
        # First check if there's an active scenario
        if self.active_scenario:
            scenario = self.scenarios.get(self.active_scenario)
            if scenario and scenario.active:
                return scenario
        
        # Then check all scenarios for matching conditions
        matching_scenarios = []
        for scenario in self.scenarios.values():
            if scenario.active and scenario.condition.matches(headers, query_params, body, path, method):
                matching_scenarios.append(scenario)
        
        if matching_scenarios:
            # For A/B testing, randomly select from matching scenarios
            if any(s.scenario_type == ScenarioType.A_B_TEST for s in matching_scenarios):
                return random.choice(matching_scenarios)
            # Otherwise, return the first matching scenario
            return matching_scenarios[0]
        
        # Return default scenario
        return self.scenarios.get(self.default_scenario)
    
    def get_response_for_path(self, path: str, headers: Dict, query_params: Dict, body: Any, method: str) -> Optional[ScenarioResponse]:
        """Get the appropriate response for a path based on the matching scenario."""
        scenario = self.get_matching_scenario(headers, query_params, body, path, method)
        if scenario:
            return scenario.responses.get(path)
        return None
    
    def create_happy_path_scenario(self) -> Scenario:
        """Create a default happy path scenario."""
        return Scenario(
            name="happy_path",
            description="Default happy path scenario with successful responses",
            scenario_type=ScenarioType.HAPPY_PATH,
            condition=ScenarioCondition(),
            responses={},
            metadata={"auto_generated": True}
        )
    
    def create_error_scenario(self, error_type: str = "server_error") -> Scenario:
        """Create an error scenario."""
        error_responses = {
            "server_error": ScenarioResponse(
                status_code=500,
                body={"error": "Internal Server Error", "code": "INTERNAL_ERROR"},
                delay=0.5
            ),
            "not_found": ScenarioResponse(
                status_code=404,
                body={"error": "Resource Not Found", "code": "NOT_FOUND"}
            ),
            "unauthorized": ScenarioResponse(
                status_code=401,
                body={"error": "Unauthorized", "code": "UNAUTHORIZED"}
            ),
            "rate_limited": ScenarioResponse(
                status_code=429,
                body={"error": "Rate Limit Exceeded", "code": "RATE_LIMITED"},
                headers={"Retry-After": "60"}
            )
        }
        
        return Scenario(
            name=f"error_{error_type}",
            description=f"Error scenario for {error_type}",
            scenario_type=ScenarioType.ERROR_SCENARIO,
            condition=ScenarioCondition(),
            responses={path: error_responses[error_type] for path in ["*"]},
            metadata={"error_type": error_type}
        )
    
    def create_performance_test_scenario(self, delay_range: tuple = (1, 5)) -> Scenario:
        """Create a performance testing scenario with delays."""
        return Scenario(
            name="performance_test",
            description="Performance testing scenario with random delays",
            scenario_type=ScenarioType.PERFORMANCE_TEST,
            condition=ScenarioCondition(),
            responses={
                "*": ScenarioResponse(
                    status_code=200,
                    body={"message": "Performance test response"},
                    delay=random.uniform(*delay_range)
                )
            },
            metadata={"delay_range": delay_range}
        )
    
    def create_a_b_test_scenario(self, variant_a_probability: float = 0.5) -> Scenario:
        """Create an A/B testing scenario."""
        return Scenario(
            name="a_b_test",
            description="A/B testing scenario with two variants",
            scenario_type=ScenarioType.A_B_TEST,
            condition=ScenarioCondition(probability=1.0),
            responses={
                "variant_a": ScenarioResponse(
                    status_code=200,
                    body={"variant": "A", "message": "Variant A response"}
                ),
                "variant_b": ScenarioResponse(
                    status_code=200,
                    body={"variant": "B", "message": "Variant B response"}
                )
            },
            metadata={"variant_a_probability": variant_a_probability}
        )
    
    def export_scenarios(self, format: str = "json") -> str:
        """Export scenarios to various formats."""
        if format == "json":
            scenarios_data = {}
            for name, scenario in self.scenarios.items():
                scenarios_data[name] = {
                    "name": scenario.name,
                    "description": scenario.description,
                    "scenario_type": scenario.scenario_type.value,
                    "active": scenario.active,
                    "metadata": scenario.metadata,
                    "responses": {
                        path: {
                            "status_code": resp.status_code,
                            "headers": resp.headers,
                            "body": resp.body,
                            "delay": resp.delay,
                            "error_message": resp.error_message,
                            "dynamic": resp.dynamic
                        }
                        for path, resp in scenario.responses.items()
                    }
                }
            return json.dumps(scenarios_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_scenarios(self, data: str, format: str = "json"):
        """Import scenarios from various formats."""
        if format == "json":
            scenarios_data = json.loads(data)
            for name, scenario_data in scenarios_data.items():
                scenario = Scenario(
                    name=scenario_data["name"],
                    description=scenario_data["description"],
                    scenario_type=ScenarioType(scenario_data["scenario_type"]),
                    condition=ScenarioCondition(),  # Default condition
                    responses={
                        path: ScenarioResponse(**resp_data)
                        for path, resp_data in scenario_data["responses"].items()
                    },
                    metadata=scenario_data.get("metadata", {}),
                    active=scenario_data.get("active", True)
                )
                self.add_scenario(scenario)
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def get_scenario_statistics(self) -> Dict[str, Any]:
        """Get statistics about scenario usage."""
        stats = {
            "total_scenarios": len(self.scenarios),
            "active_scenarios": len([s for s in self.scenarios.values() if s.active]),
            "scenario_types": {},
            "current_active": self.active_scenario,
            "usage_history": self.scenario_history[-100:]  # Last 100 activations
        }
        
        for scenario in self.scenarios.values():
            scenario_type = scenario.scenario_type.value
            stats["scenario_types"][scenario_type] = stats["scenario_types"].get(scenario_type, 0) + 1
        
        return stats
    
    def _log_scenario_activation(self, scenario_name: str):
        """Log scenario activation for analytics."""
        self.scenario_history.append({
            "action": "activated",
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_scenario_deactivation(self, scenario_name: str):
        """Log scenario deactivation for analytics."""
        self.scenario_history.append({
            "action": "deactivated",
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat()
        })


# Global scenario manager instance
scenario_manager = ScenarioManager() 