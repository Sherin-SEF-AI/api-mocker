"""
Advanced Testing Framework for API-Mocker.
"""

import json
import asyncio
import time
import statistics
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import requests
import yaml

try:
    from .ai_generator import AIGenerationManager
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Represents a test case."""
    name: str
    description: str
    method: str
    url: str
    headers: Dict = None
    body: Dict = None
    expected_status: int = 200
    expected_schema: Dict = None
    assertions: List[Dict] = None
    timeout: int = 30
    retries: int = 0
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.body is None:
            self.body = {}
        if self.assertions is None:
            self.assertions = []

@dataclass
class TestSuite:
    """Represents a test suite."""
    name: str
    description: str
    base_url: str
    test_cases: List[TestCase]
    setup_hooks: List[Dict] = None
    teardown_hooks: List[Dict] = None
    variables: Dict = None
    
    def __post_init__(self):
        if self.setup_hooks is None:
            self.setup_hooks = []
        if self.teardown_hooks is None:
            self.teardown_hooks = []
        if self.variables is None:
            self.variables = {}

@dataclass
class TestResult:
    """Represents a test result."""
    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float
    response: Dict = None
    error: str = None
    assertions: List[Dict] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.assertions is None:
            self.assertions = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class PerformanceTest:
    """Represents a performance test."""
    name: str
    test_case: TestCase
    concurrent_users: int
    duration_seconds: int
    ramp_up_seconds: int = 0
    target_rps: Optional[float] = None

@dataclass
class PerformanceResult:
    """Represents performance test results."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    duration: float
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class TestRunner:
    """Runs test suites and individual tests."""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.session = requests.Session()
        self.ai_manager = AIGenerationManager() if AI_AVAILABLE else None
    
    def run_test_case(self, test_case: TestCase, base_url: str = "") -> TestResult:
        """Run a single test case."""
        start_time = time.time()
        
        try:
            # Prepare URL
            url = base_url + test_case.url if base_url else test_case.url
            
            # Prepare headers
            headers = test_case.headers.copy()
            
            # Prepare body
            body = test_case.body.copy() if test_case.body else None
            
            # Make request
            response = self.session.request(
                method=test_case.method,
                url=url,
                headers=headers,
                json=body,
                timeout=test_case.timeout
            )
            
            duration = time.time() - start_time
            
            # Create response dict
            response_dict = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            # Run assertions
            assertions = self._run_assertions(test_case, response_dict)
            
            # Determine status
            status = "passed"
            if any(not assertion["passed"] for assertion in assertions):
                status = "failed"
            
            return TestResult(
                test_name=test_case.name,
                status=status,
                duration=duration,
                response=response_dict,
                assertions=assertions
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_case.name,
                status="error",
                duration=duration,
                error=str(e)
            )
    
    def run_test_suite(self, test_suite: TestSuite) -> List[TestResult]:
        """Run a complete test suite."""
        results = []
        
        # Run setup hooks
        self._run_hooks(test_suite.setup_hooks)
        
        # Set variables
        self.variables.update(test_suite.variables)
        
        # Run test cases
        for test_case in test_suite.test_cases:
            result = self.run_test_case(test_case, test_suite.base_url)
            results.append(result)
            
            # Update variables with response data if needed
            if result.response:
                self.variables[f"{test_case.name}_response"] = result.response
        
        # Run teardown hooks
        self._run_hooks(test_suite.teardown_hooks)
        
        return results
    
    def _run_assertions(self, test_case: TestCase, response: Dict) -> List[Dict]:
        """Run assertions on the response."""
        assertions = []
        
        # Status code assertion
        status_assertion = {
            "name": "Status Code",
            "expected": test_case.expected_status,
            "actual": response["status_code"],
            "passed": response["status_code"] == test_case.expected_status
        }
        assertions.append(status_assertion)
        
        # Custom assertions
        for assertion in test_case.assertions:
            assertion_result = self._evaluate_assertion(assertion, response)
            assertions.append(assertion_result)
        
        return assertions
    
    def _evaluate_assertion(self, assertion: Dict, response: Dict) -> Dict:
        """Evaluate a single assertion."""
        assertion_type = assertion.get("type", "json_path")
        
        if assertion_type == "json_path":
            return self._evaluate_json_path_assertion(assertion, response)
        elif assertion_type == "header":
            return self._evaluate_header_assertion(assertion, response)
        elif assertion_type == "contains":
            return self._evaluate_contains_assertion(assertion, response)
        elif assertion_type == "regex":
            return self._evaluate_regex_assertion(assertion, response)
        else:
            return {
                "name": assertion.get("name", "Unknown"),
                "passed": False,
                "error": f"Unknown assertion type: {assertion_type}"
            }
    
    def _evaluate_json_path_assertion(self, assertion: Dict, response: Dict) -> Dict:
        """Evaluate JSON path assertion."""
        try:
            json_path = assertion["path"]
            expected_value = assertion.get("value")
            operator = assertion.get("operator", "equals")
            
            # Simple JSON path evaluation (in production, use jsonpath-ng)
            path_parts = json_path.split(".")
            current = response.get("body", {})
            
            for part in path_parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)]
                else:
                    current = None
                    break
            
            # Evaluate operator
            passed = False
            if operator == "equals":
                passed = current == expected_value
            elif operator == "not_equals":
                passed = current != expected_value
            elif operator == "exists":
                passed = current is not None
            elif operator == "not_exists":
                passed = current is None
            elif operator == "greater_than":
                passed = current > expected_value
            elif operator == "less_than":
                passed = current < expected_value
            
            return {
                "name": assertion.get("name", f"JSON Path: {json_path}"),
                "expected": expected_value,
                "actual": current,
                "passed": passed
            }
            
        except Exception as e:
            return {
                "name": assertion.get("name", "JSON Path Assertion"),
                "passed": False,
                "error": str(e)
            }
    
    def _evaluate_header_assertion(self, assertion: Dict, response: Dict) -> Dict:
        """Evaluate header assertion."""
        header_name = assertion["header"]
        expected_value = assertion.get("value")
        operator = assertion.get("operator", "equals")
        
        actual_value = response.get("headers", {}).get(header_name)
        
        passed = False
        if operator == "equals":
            passed = actual_value == expected_value
        elif operator == "contains":
            passed = expected_value in actual_value if actual_value else False
        elif operator == "exists":
            passed = actual_value is not None
        
        return {
            "name": assertion.get("name", f"Header: {header_name}"),
            "expected": expected_value,
            "actual": actual_value,
            "passed": passed
        }
    
    def _evaluate_contains_assertion(self, assertion: Dict, response: Dict) -> Dict:
        """Evaluate contains assertion."""
        expected_text = assertion["text"]
        response_text = str(response.get("body", ""))
        
        passed = expected_text in response_text
        
        return {
            "name": assertion.get("name", f"Contains: {expected_text}"),
            "expected": expected_text,
            "actual": response_text[:100] + "..." if len(response_text) > 100 else response_text,
            "passed": passed
        }
    
    def _evaluate_regex_assertion(self, assertion: Dict, response: Dict) -> Dict:
        """Evaluate regex assertion."""
        import re
        
        pattern = assertion["pattern"]
        response_text = str(response.get("body", ""))
        
        match = re.search(pattern, response_text)
        passed = match is not None
        
        return {
            "name": assertion.get("name", f"Regex: {pattern}"),
            "expected": pattern,
            "actual": response_text[:100] + "..." if len(response_text) > 100 else response_text,
            "passed": passed
        }
    
    def _run_hooks(self, hooks: List[Dict]):
        """Run setup/teardown hooks."""
        for hook in hooks:
            hook_type = hook.get("type", "http")
            
            if hook_type == "http":
                self._run_http_hook(hook)
            elif hook_type == "variable":
                self._run_variable_hook(hook)
    
    def _run_http_hook(self, hook: Dict):
        """Run HTTP hook."""
        try:
            method = hook.get("method", "GET")
            url = hook["url"]
            headers = hook.get("headers", {})
            body = hook.get("body")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=body
            )
            
            # Store response in variables if needed
            if "store_as" in hook:
                self.variables[hook["store_as"]] = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
                
        except Exception as e:
            logger.error(f"HTTP hook failed: {e}")
    
    def _run_variable_hook(self, hook: Dict):
        """Run variable hook."""
        variable_name = hook["name"]
        value = hook["value"]
        
        self.variables[variable_name] = value

class PerformanceTester:
    """Runs performance tests."""
    
    def __init__(self):
        self.session = requests.Session()
    
    def run_performance_test(self, perf_test: PerformanceTest) -> PerformanceResult:
        """Run a performance test."""
        start_time = time.time()
        results = []
        
        # Calculate ramp-up
        if perf_test.ramp_up_seconds > 0:
            users_per_second = perf_test.concurrent_users / perf_test.ramp_up_seconds
        else:
            users_per_second = perf_test.concurrent_users
        
        # Run concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=perf_test.concurrent_users) as executor:
            futures = []
            
            for i in range(perf_test.concurrent_users):
                # Ramp up delay
                if perf_test.ramp_up_seconds > 0:
                    delay = i / users_per_second
                    time.sleep(delay)
                
                future = executor.submit(self._make_request, perf_test.test_case)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures, timeout=perf_test.duration_seconds):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "duration": 0})
        
        duration = time.time() - start_time
        
        return self._calculate_performance_metrics(results, duration)
    
    def _make_request(self, test_case: TestCase) -> Dict:
        """Make a single request for performance testing."""
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=test_case.method,
                url=test_case.url,
                headers=test_case.headers,
                json=test_case.body,
                timeout=test_case.timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "status_code": response.status_code,
                "duration": duration,
                "success": response.status_code < 400
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                "error": str(e),
                "duration": duration,
                "success": False
            }
    
    def _calculate_performance_metrics(self, results: List[Dict], duration: float) -> PerformanceResult:
        """Calculate performance metrics from results."""
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", False)]
        
        durations = [r["duration"] for r in results if "duration" in r]
        
        if not durations:
            return PerformanceResult(
                test_name="Performance Test",
                total_requests=len(results),
                successful_requests=0,
                failed_requests=len(results),
                average_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                error_rate=100.0,
                duration=duration
            )
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        p95_index = int(len(sorted_durations) * 0.95)
        p99_index = int(len(sorted_durations) * 0.99)
        
        return PerformanceResult(
            test_name="Performance Test",
            total_requests=len(results),
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            average_response_time=statistics.mean(durations),
            min_response_time=min(durations),
            max_response_time=max(durations),
            p95_response_time=sorted_durations[p95_index] if p95_index < len(sorted_durations) else max(durations),
            p99_response_time=sorted_durations[p99_index] if p99_index < len(sorted_durations) else max(durations),
            requests_per_second=len(results) / duration,
            error_rate=(len(failed_requests) / len(results)) * 100,
            duration=duration
        )

class TestGenerator:
    """Generates test cases automatically."""
    
    def __init__(self):
        self.ai_manager = AIGenerationManager() if AI_AVAILABLE else None
    
    def generate_tests_from_config(self, config: Dict) -> TestSuite:
        """Generate test cases from API configuration."""
        test_cases = []
        
        for route in config.get("routes", []):
            test_case = self._create_test_case_from_route(route)
            test_cases.append(test_case)
        
        return TestSuite(
            name="Auto-generated Test Suite",
            description="Automatically generated tests from API configuration",
            base_url=config.get("server", {}).get("base_url", "http://localhost:8000"),
            test_cases=test_cases
        )
    
    def _create_test_case_from_route(self, route: Dict) -> TestCase:
        """Create a test case from a route configuration."""
        method = route.get("method", "GET")
        path = route.get("path", "/")
        response = route.get("response", {})
        
        # Generate test name
        test_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
        
        # Create assertions based on response
        assertions = []
        if isinstance(response, dict):
            assertions.append({
                "type": "json_path",
                "path": "$",
                "operator": "exists",
                "name": "Response is JSON object"
            })
        
        return TestCase(
            name=test_name,
            description=f"Test for {method} {path}",
            method=method,
            url=path,
            expected_status=200,
            assertions=assertions
        )
    
    def generate_ai_tests(self, api_description: str, endpoints: List[str]) -> TestSuite:
        """Generate test cases using AI."""
        if not self.ai_manager:
            raise ValueError("AI generation not available")
        
        prompt = f"""
        Generate comprehensive test cases for the following API:
        
        Description: {api_description}
        Endpoints: {', '.join(endpoints)}
        
        Generate test cases that cover:
        1. Happy path scenarios
        2. Error cases
        3. Edge cases
        4. Validation tests
        
        Return the test cases in JSON format.
        """
        
        result = self.ai_manager.generate_mock_data(
            prompt=prompt,
            endpoint="/generate-tests",
            count=1
        )
        
        # Parse AI response and convert to test cases
        # This is a simplified implementation
        test_cases = []
        for i, endpoint in enumerate(endpoints):
            test_case = TestCase(
                name=f"AI_Generated_Test_{i+1}",
                description=f"AI-generated test for {endpoint}",
                method="GET",
                url=endpoint,
                expected_status=200
            )
            test_cases.append(test_case)
        
        return TestSuite(
            name="AI-Generated Test Suite",
            description="Test cases generated using AI",
            base_url="http://localhost:8000",
            test_cases=test_cases
        )

class TestingFramework:
    """Main testing framework class."""
    
    def __init__(self):
        self.test_runner = TestRunner()
        self.performance_tester = PerformanceTester()
        self.test_generator = TestGenerator()
    
    def run_tests_from_file(self, test_file: str) -> List[TestResult]:
        """Run tests from a test file."""
        with open(test_file, 'r') as f:
            if test_file.endswith('.yaml') or test_file.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        test_suite = self._load_test_suite_from_data(data)
        return self.test_runner.run_test_suite(test_suite)
    
    def run_performance_test_from_file(self, perf_file: str) -> PerformanceResult:
        """Run performance test from a file."""
        with open(perf_file, 'r') as f:
            if perf_file.endswith('.yaml') or perf_file.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        perf_test = self._load_performance_test_from_data(data)
        return self.performance_tester.run_performance_test(perf_test)
    
    def generate_tests(self, config_file: str, output_file: str):
        """Generate tests from configuration."""
        with open(config_file, 'r') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        test_suite = self.test_generator.generate_tests_from_config(config)
        
        # Save test suite
        with open(output_file, 'w') as f:
            if output_file.endswith('.yaml') or output_file.endswith('.yml'):
                yaml.dump(asdict(test_suite), f, indent=2)
            else:
                json.dump(asdict(test_suite), f, indent=2)
    
    def _load_test_suite_from_data(self, data: Dict) -> TestSuite:
        """Load test suite from data dictionary."""
        test_cases = []
        for test_data in data.get("test_cases", []):
            test_case = TestCase(
                name=test_data.get("name", "Unnamed Test"),
                description=test_data.get("description", ""),
                method=test_data.get("method", "GET"),
                url=test_data.get("url", "/"),
                headers=test_data.get("headers", {}),
                body=test_data.get("body", {}),
                expected_status=test_data.get("expected_status", 200),
                expected_schema=test_data.get("expected_schema"),
                assertions=test_data.get("assertions", []),
                timeout=test_data.get("timeout", 30),
                retries=test_data.get("retries", 0)
            )
            test_cases.append(test_case)
        
        return TestSuite(
            name=data.get("name", "Test Suite"),
            description=data.get("description", ""),
            base_url=data.get("base_url", ""),
            test_cases=test_cases,
            setup_hooks=data.get("setup_hooks", []),
            teardown_hooks=data.get("teardown_hooks", []),
            variables=data.get("variables", {})
        )
    
    def _load_performance_test_from_data(self, data: Dict) -> PerformanceTest:
        """Load performance test from data dictionary."""
        test_case_data = data.get("test_case", {})
        test_case = TestCase(
            name=test_case_data.get("name", "Performance Test Case"),
            description=test_case_data.get("description", ""),
            method=test_case_data.get("method", "GET"),
            url=test_case_data.get("url", "/"),
            headers=test_case_data.get("headers", {}),
            body=test_case_data.get("body", {}),
            expected_status=test_case_data.get("expected_status", 200),
            expected_schema=test_case_data.get("expected_schema"),
            assertions=test_case_data.get("assertions", []),
            timeout=test_case_data.get("timeout", 30),
            retries=test_case_data.get("retries", 0)
        )
        
        return PerformanceTest(
            name=data.get("name", "Performance Test"),
            test_case=test_case,
            concurrent_users=data.get("concurrent_users", 10),
            duration_seconds=data.get("duration_seconds", 60),
            ramp_up_seconds=data.get("ramp_up_seconds", 0),
            target_rps=data.get("target_rps")
        ) 