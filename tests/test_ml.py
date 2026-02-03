import pytest
import numpy as np
from datetime import datetime
from api_mocker.ml_integration import (
    MLIntegration, MLModelType, PredictionType, 
    PredictionRequest, FeatureExtractor, TrainingData
)

@pytest.fixture
def ml_integration():
    return MLIntegration()

def test_feature_extractor():
    extractor = FeatureExtractor()
    request = {
        "path": "/api/users/1?q=test",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "body": ""
    }
    
    features = extractor.extract_request_features(request)
    
    assert "path_length" in features
    assert features["has_query_params"] == 1
    assert features["has_auth_header"] == 1
    assert features["method_encoded"] >= 0

def test_ml_training_flow(ml_integration):
    """Test full training loop for simple regression"""
    
    # 1. Record some fake data
    for _ in range(105): # Need > 100 samples
        ml_integration.record_request(
            request_data={
                "path": "/api/test", 
                "method": "GET", 
                "headers": {}, 
                "body": ""
            },
            response_data={
                "status_code": 200, 
                "body": "success"
            }
        )
        
    # 2. Train Models
    results = ml_integration.train_models()
    
    assert "response_time" in results
    assert results["response_time"]["success"] is True
    assert results["response_time"]["training_samples"] >= 100
    
    assert "error_probability" in results
    assert results["error_probability"]["success"] is True
    
    assert "anomaly_detector" in results
    assert results["anomaly_detector"]["fitted"] is True

def test_predictions(ml_integration):
    """Test prediction logic"""
    # Needs trained models first, or at least models present. 
    # train_models creates them.
    
    # Let's manually add a dummy model for isolation
    from api_mocker.ml_integration import create_ml_model
    
    model = create_ml_model(
        name="response_time_predictor",
        model_type=MLModelType.REGRESSION,
        features=['path_length'],
        target="time"
    )
    
    # Force fit with dummy data
    X = np.array([[1], [10]])
    y = np.array([0.1, 0.5])
    model.model.fit(X, y)
    model.accuracy = 0.9
    
    # Predict
    req = {"path": "short", "method": "GET"} # path_length=5
    # The internal predict method extracts features.
    # FeatureExtractor calculates path_length.
    
    predicted_time = ml_integration.predict_response_time(req)
    assert isinstance(predicted_time, float)
    assert predicted_time > 0

def test_smart_response(ml_integration):
    """Test smart response generation"""
    # Again, requires models to be vaguely functional
    # But even without training, it should return defaults (though maybe warning)
    # The code handles uninitialized models gracefully-ish?
    # Actually, LinearRegression needs fit() before predict() usually.
    # Let's see how handled.
    
    # To test safely, we should fit them.
    for _ in range(105):
        ml_integration.record_request(
            {"path": "/api", "headers": {}},
            {"status_code": 200}
        )
    ml_integration.train_models()
    
    response = ml_integration.generate_smart_response({"path": "/api", "headers": {}})
    
    assert response["status_code"] in [200, 400, 401, 403, 404, 500]
    assert "X-ML-Predicted" in response["headers"]
    assert "predicted_response_time" in response["body"]
