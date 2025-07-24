"""
Smart Response Matching System

Provides intelligent response selection based on:
- Request body analysis for response selection
- Header-based routing
- Query parameter matching
- Custom logic for response selection
- Dynamic response generation based on request context
"""

import json
import re
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import operator
from enum import Enum


class MatchType(Enum):
    EXACT = "exact"
    REGEX = "regex"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    CUSTOM = "custom"


@dataclass
class MatchCondition:
    """Defines a condition for matching requests."""
    field: str  # e.g., "body.user_id", "headers.authorization", "query.page"
    match_type: MatchType
    value: Any = None
    custom_function: Optional[Callable] = None
    case_sensitive: bool = True
    
    def matches(self, request_data: Dict[str, Any]) -> bool:
        """Check if the condition matches the request data."""
        field_value = self._extract_field_value(request_data, self.field)
        
        if self.match_type == MatchType.CUSTOM and self.custom_function:
            return self.custom_function(field_value, request_data)
        
        if self.match_type == MatchType.EXISTS:
            return field_value is not None
        
        if self.match_type == MatchType.NOT_EXISTS:
            return field_value is None
        
        if field_value is None:
            return False
        
        if self.match_type == MatchType.EXACT:
            return field_value == self.value
        
        if self.match_type == MatchType.REGEX:
            if not isinstance(field_value, str):
                return False
            flags = 0 if self.case_sensitive else re.IGNORECASE
            return bool(re.search(self.value, field_value, flags))
        
        if self.match_type == MatchType.CONTAINS:
            if isinstance(field_value, str) and isinstance(self.value, str):
                if not self.case_sensitive:
                    return self.value.lower() in field_value.lower()
                return self.value in field_value
            elif isinstance(field_value, (list, dict)):
                return self.value in field_value
            return False
        
        if self.match_type == MatchType.GREATER_THAN:
            return self._compare_values(field_value, self.value, operator.gt)
        
        if self.match_type == MatchType.LESS_THAN:
            return self._compare_values(field_value, self.value, operator.lt)
        
        if self.match_type == MatchType.EQUALS:
            return field_value == self.value
        
        if self.match_type == MatchType.NOT_EQUALS:
            return field_value != self.value
        
        return False
    
    def _extract_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extract a value from nested data using dot notation."""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def _compare_values(self, a: Any, b: Any, op: Callable) -> bool:
        """Compare two values using the specified operator."""
        try:
            # Try to convert to numbers for comparison
            if isinstance(a, str) and a.isdigit():
                a = int(a)
            if isinstance(b, str) and b.isdigit():
                b = int(b)
            
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return op(a, b)
            
            # Fallback to string comparison
            return op(str(a), str(b))
        except (ValueError, TypeError):
            return False


@dataclass
class ResponseRule:
    """Defines a response rule with conditions and response."""
    name: str
    conditions: List[MatchCondition]
    response: Dict[str, Any]
    priority: int = 0  # Higher priority rules are checked first
    weight: float = 1.0  # For weighted random selection
    metadata: Dict[str, Any] = field(default_factory=dict)


class SmartResponseMatcher:
    """Intelligent response matching system."""
    
    def __init__(self):
        self.rules: List[ResponseRule] = []
        self.default_response: Optional[Dict[str, Any]] = None
        self.match_history: List[Dict] = []
    
    def add_rule(self, rule: ResponseRule):
        """Add a response rule."""
        self.rules.append(rule)
        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def set_default_response(self, response: Dict[str, Any]):
        """Set the default response when no rules match."""
        self.default_response = response
    
    def find_matching_response(self, request_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[ResponseRule]]:
        """Find the best matching response for the request."""
        matching_rules = []
        
        for rule in self.rules:
            if self._rule_matches(rule, request_data):
                matching_rules.append(rule)
        
        if not matching_rules:
            self._log_match("no_match", None, request_data)
            return self.default_response, None
        
        # If multiple rules match, use weighted random selection
        if len(matching_rules) > 1:
            selected_rule = self._select_weighted_rule(matching_rules)
        else:
            selected_rule = matching_rules[0]
        
        self._log_match("match", selected_rule, request_data)
        return selected_rule.response, selected_rule
    
    def _rule_matches(self, rule: ResponseRule, request_data: Dict[str, Any]) -> bool:
        """Check if a rule matches the request data."""
        for condition in rule.conditions:
            if not condition.matches(request_data):
                return False
        return True
    
    def _select_weighted_rule(self, rules: List[ResponseRule]) -> ResponseRule:
        """Select a rule using weighted random selection."""
        import random
        
        total_weight = sum(rule.weight for rule in rules)
        if total_weight == 0:
            return rules[0]  # Fallback to first rule
        
        rand = random.uniform(0, total_weight)
        current_weight = 0
        
        for rule in rules:
            current_weight += rule.weight
            if rand <= current_weight:
                return rule
        
        return rules[-1]  # Fallback to last rule
    
    def create_user_type_rule(self, user_type: str, response: Dict[str, Any]) -> ResponseRule:
        """Create a rule based on user type in request body."""
        return ResponseRule(
            name=f"user_type_{user_type}",
            conditions=[
                MatchCondition(
                    field="body.user_type",
                    match_type=MatchType.EXACT,
                    value=user_type
                )
            ],
            response=response,
            priority=10
        )
    
    def create_api_version_rule(self, version: str, response: Dict[str, Any]) -> ResponseRule:
        """Create a rule based on API version in headers."""
        return ResponseRule(
            name=f"api_version_{version}",
            conditions=[
                MatchCondition(
                    field="headers.x-api-version",
                    match_type=MatchType.EXACT,
                    value=version
                )
            ],
            response=response,
            priority=15
        )
    
    def create_premium_user_rule(self, response: Dict[str, Any]) -> ResponseRule:
        """Create a rule for premium users."""
        return ResponseRule(
            name="premium_user",
            conditions=[
                MatchCondition(
                    field="body.user_type",
                    match_type=MatchType.EXACT,
                    value="premium"
                ),
                MatchCondition(
                    field="headers.authorization",
                    match_type=MatchType.EXISTS
                )
            ],
            response=response,
            priority=20
        )
    
    def create_rate_limit_rule(self, threshold: int, response: Dict[str, Any]) -> ResponseRule:
        """Create a rule for rate limiting based on request count."""
        def rate_limit_check(field_value, request_data):
            # This would typically check against a rate limiter
            # For now, we'll use a simple example
            request_count = request_data.get("request_count", 0)
            return request_count > threshold
        
        return ResponseRule(
            name="rate_limited",
            conditions=[
                MatchCondition(
                    field="request_count",
                    match_type=MatchType.CUSTOM,
                    custom_function=rate_limit_check
                )
            ],
            response=response,
            priority=25
        )
    
    def create_error_rule(self, error_condition: str, response: Dict[str, Any]) -> ResponseRule:
        """Create a rule for error scenarios."""
        error_conditions = {
            "invalid_token": MatchCondition(
                field="headers.authorization",
                match_type=MatchType.REGEX,
                value=r"invalid|expired"
            ),
            "missing_required": MatchCondition(
                field="body",
                match_type=MatchType.CUSTOM,
                custom_function=lambda body, _: not body or not isinstance(body, dict)
            ),
            "malformed_request": MatchCondition(
                field="headers.content-type",
                match_type=MatchType.NOT_EQUALS,
                value="application/json"
            )
        }
        
        return ResponseRule(
            name=f"error_{error_condition}",
            conditions=[error_conditions.get(error_condition)],
            response=response,
            priority=30
        )
    
    def create_performance_rule(self, delay_range: Tuple[float, float], response: Dict[str, Any]) -> ResponseRule:
        """Create a rule for performance testing with delays."""
        import random
        
        response_with_delay = response.copy()
        response_with_delay["delay"] = random.uniform(*delay_range)
        
        return ResponseRule(
            name="performance_test",
            conditions=[
                MatchCondition(
                    field="headers.x-performance-test",
                    match_type=MatchType.EXISTS
                )
            ],
            response=response_with_delay,
            priority=5
        )
    
    def export_rules(self, format: str = "json") -> str:
        """Export rules to various formats."""
        if format == "json":
            rules_data = {
                "rules": [
                    {
                        "name": rule.name,
                        "priority": rule.priority,
                        "weight": rule.weight,
                        "metadata": rule.metadata,
                        "conditions": [
                            {
                                "field": cond.field,
                                "match_type": cond.match_type.value,
                                "value": cond.value,
                                "case_sensitive": cond.case_sensitive
                            }
                            for cond in rule.conditions
                        ],
                        "response": rule.response
                    }
                    for rule in self.rules
                ],
                "default_response": self.default_response
            }
            return json.dumps(rules_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_rules(self, data: str, format: str = "json"):
        """Import rules from various formats."""
        if format == "json":
            rules_data = json.loads(data)
            
            # Clear existing rules
            self.rules = []
            
            # Import rules
            for rule_data in rules_data.get("rules", []):
                conditions = [
                    MatchCondition(
                        field=cond["field"],
                        match_type=MatchType(cond["match_type"]),
                        value=cond.get("value"),
                        case_sensitive=cond.get("case_sensitive", True)
                    )
                    for cond in rule_data["conditions"]
                ]
                
                rule = ResponseRule(
                    name=rule_data["name"],
                    conditions=conditions,
                    response=rule_data["response"],
                    priority=rule_data.get("priority", 0),
                    weight=rule_data.get("weight", 1.0),
                    metadata=rule_data.get("metadata", {})
                )
                self.add_rule(rule)
            
            # Set default response
            if "default_response" in rules_data:
                self.default_response = rules_data["default_response"]
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def get_matching_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule matching."""
        stats = {
            "total_rules": len(self.rules),
            "match_history": self.match_history[-100:],  # Last 100 matches
            "rule_usage": {},
            "no_match_count": 0
        }
        
        # Count rule usage
        for match in self.match_history:
            if match["result"] == "match":
                rule_name = match["rule_name"]
                stats["rule_usage"][rule_name] = stats["rule_usage"].get(rule_name, 0) + 1
            else:
                stats["no_match_count"] += 1
        
        return stats
    
    def _log_match(self, result: str, rule: Optional[ResponseRule], request_data: Dict[str, Any]):
        """Log match results for analytics."""
        self.match_history.append({
            "result": result,
            "rule_name": rule.name if rule else None,
            "timestamp": datetime.now().isoformat(),
            "request_path": request_data.get("path"),
            "request_method": request_data.get("method")
        })


# Global smart matcher instance
smart_matcher = SmartResponseMatcher() 