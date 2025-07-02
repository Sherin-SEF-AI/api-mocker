#!/usr/bin/env python3

from src.api_mocker.core import AdvancedRouter, RouteConfig

def test_route_matching():
    router = AdvancedRouter()
    
    # Add a test route
    route = RouteConfig(
        path="api/health",
        method="GET",
        response={"message": "test"}
    )
    router.add_route(route)
    
    print(f"Added route: {route.method} {route.path}")
    print(f"Total routes: {len(router.routes)}")
    
    # Test route matching
    test_paths = ["api/health", "/api/health", "api/health/", "/api/health/"]
    
    for test_path in test_paths:
        found_route = router.find_route(test_path, "GET")
        print(f"Path '{test_path}' -> {'Found' if found_route else 'Not found'}")

if __name__ == "__main__":
    test_route_matching() 