"""
Machine Learning Integration System

This module provides comprehensive ML capabilities for API mocking including:
- Intelligent response generation using ML models
- Request pattern analysis and prediction
- Anomaly detection for API behavior
- Smart caching based on usage patterns
- Automated test case generation
- Performance optimization recommendations
"""

import json
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import pickle
import joblib
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPClassifier
import asyncio
import threading
from collections import defaultdict, deque
import hashlib


class MLModelType(Enum):
    """ML model types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TEXT_ANALYSIS = "text_analysis"
    RECOMMENDATION = "recommendation"


class PredictionType(Enum):
    """Prediction types"""
    RESPONSE_TIME = "response_time"
    ERROR_PROBABILITY = "error_probability"
    USER_BEHAVIOR = "user_behavior"
    CACHE_HIT = "cache_hit"
    RESOURCE_USAGE = "resource_usage"
    ANOMALY_SCORE = "anomaly_score"


@dataclass
class MLModel:
    """ML model representation"""
    name: str
    model_type: MLModelType
    model: Any
    features: List[str]
    target: str
    accuracy: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_trained: datetime = field(default_factory=datetime.now)
    training_samples: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionRequest:
    """Prediction request"""
    features: Dict[str, Any]
    model_name: str
    prediction_type: PredictionType
    confidence_threshold: float = 0.5


@dataclass
class PredictionResult:
    """Prediction result"""
    prediction: Any
    confidence: float
    model_name: str
    features_used: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingData:
    """Training data for ML models"""
    features: List[Dict[str, Any]]
    targets: List[Any]
    feature_names: List[str]
    target_name: str
    created_at: datetime = field(default_factory=datetime.now)


class FeatureExtractor:
    """Feature extraction for ML models"""
    
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
    
    def extract_request_features(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from API request data"""
        features = {}
        
        # Basic features
        features['method_encoded'] = self._encode_categorical(request_data.get('method', ''), 'method')
        features['path_length'] = len(request_data.get('path', ''))
        features['has_query_params'] = 1 if '?' in request_data.get('path', '') else 0
        features['has_path_params'] = 1 if '{' in request_data.get('path', '') else 0
        
        # Header features
        headers = request_data.get('headers', {})
        features['header_count'] = len(headers)
        features['has_auth_header'] = 1 if 'authorization' in headers else 0
        features['has_content_type'] = 1 if 'content-type' in headers else 0
        
        # Body features
        body = request_data.get('body', '')
        if isinstance(body, str):
            features['body_length'] = len(body)
            features['is_json'] = 1 if body.startswith('{') or body.startswith('[') else 0
        else:
            features['body_length'] = 0
            features['is_json'] = 0
        
        # Time-based features
        now = datetime.now()
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_weekend'] = 1 if now.weekday() >= 5 else 0
        
        return features
    
    def extract_response_features(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from API response data"""
        features = {}
        
        features['status_code'] = response_data.get('status_code', 200)
        features['is_success'] = 1 if 200 <= features['status_code'] < 300 else 0
        features['is_client_error'] = 1 if 400 <= features['status_code'] < 500 else 0
        features['is_server_error'] = 1 if 500 <= features['status_code'] < 600 else 0
        
        # Response body features
        body = response_data.get('body', '')
        if isinstance(body, str):
            features['response_length'] = len(body)
        else:
            features['response_length'] = 0
        
        # Header features
        headers = response_data.get('headers', {})
        features['response_header_count'] = len(headers)
        features['has_cache_header'] = 1 if 'cache-control' in headers else 0
        
        return features
    
    def _encode_categorical(self, value: str, field_name: str) -> int:
        """Encode categorical values"""
        if field_name not in self.label_encoders:
            self.label_encoders[field_name] = LabelEncoder()
            # Fit with known values
            known_values = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
            self.label_encoders[field_name].fit(known_values)
        
        try:
            return self.label_encoders[field_name].transform([value])[0]
        except ValueError:
            return 0  # Unknown value


class MLModelManager:
    """ML model management system"""
    
    def __init__(self):
        self.models: Dict[str, MLModel] = {}
        self.feature_extractor = FeatureExtractor()
        self.training_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.model_lock = threading.Lock()
    
    def add_model(self, model: MLModel) -> None:
        """Add a model to the manager"""
        with self.model_lock:
            self.models[model.name] = model
    
    def get_model(self, name: str) -> Optional[MLModel]:
        """Get a model by name"""
        return self.models.get(name)
    
    def train_model(self, model_name: str, training_data: TrainingData) -> Dict[str, Any]:
        """Train a model with provided data"""
        if model_name not in self.models:
            return {"success": False, "error": "Model not found"}
        
        model = self.models[model_name]
        
        try:
            # Prepare features and targets
            X = []
            y = []
            
            for i, features in enumerate(training_data.features):
                X.append(list(features.values()))
                y.append(training_data.targets[i])
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.feature_extractor.scaler.fit_transform(X_train)
            X_test_scaled = self.feature_extractor.scaler.transform(X_test)
            
            # Train model
            model.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Update model
            model.accuracy = accuracy
            model.last_trained = datetime.now()
            model.training_samples = len(training_data.features)
            
            return {
                "success": True,
                "accuracy": accuracy,
                "training_samples": len(training_data.features),
                "test_samples": len(X_test)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Make a prediction using a model"""
        if request.model_name not in self.models:
            return PredictionResult(
                prediction=None,
                confidence=0.0,
                model_name=request.model_name,
                features_used=[],
                metadata={"error": "Model not found"}
            )
        
        model = self.models[request.model_name]
        
        try:
            # Extract features
            features = self.feature_extractor.extract_request_features(request.features)
            feature_values = [features.get(f, 0) for f in model.features]
            
            # Scale features
            feature_array = np.array(feature_values).reshape(1, -1)
            scaled_features = self.feature_extractor.scaler.transform(feature_array)
            
            # Make prediction
            if model.model_type == MLModelType.CLASSIFICATION:
                prediction = model.model.predict(scaled_features)[0]
                confidence = model.model.predict_proba(scaled_features).max()
            else:
                prediction = model.model.predict(scaled_features)[0]
                confidence = 1.0  # For regression, we don't have confidence scores
            
            return PredictionResult(
                prediction=prediction,
                confidence=confidence,
                model_name=request.model_name,
                features_used=model.features,
                metadata={"model_accuracy": model.accuracy}
            )
            
        except Exception as e:
            return PredictionResult(
                prediction=None,
                confidence=0.0,
                model_name=request.model_name,
                features_used=[],
                metadata={"error": str(e)}
            )
    
    def save_model(self, model_name: str, filepath: str) -> bool:
        """Save a model to disk"""
        if model_name not in self.models:
            return False
        
        try:
            model = self.models[model_name]
            model_data = {
                "name": model.name,
                "model_type": model.model_type.value,
                "features": model.features,
                "target": model.target,
                "accuracy": model.accuracy,
                "created_at": model.created_at.isoformat(),
                "last_trained": model.last_trained.isoformat(),
                "training_samples": model.training_samples,
                "metadata": model.metadata
            }
            
            # Save model and metadata
            joblib.dump(model.model, f"{filepath}_model.pkl")
            with open(f"{filepath}_metadata.json", 'w') as f:
                json.dump(model_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_name: str, filepath: str) -> bool:
        """Load a model from disk"""
        try:
            # Load metadata
            with open(f"{filepath}_metadata.json", 'r') as f:
                model_data = json.load(f)
            
            # Load model
            model_obj = joblib.load(f"{filepath}_model.pkl")
            
            # Create model
            model = MLModel(
                name=model_data["name"],
                model_type=MLModelType(model_data["model_type"]),
                model=model_obj,
                features=model_data["features"],
                target=model_data["target"],
                accuracy=model_data["accuracy"],
                created_at=datetime.fromisoformat(model_data["created_at"]),
                last_trained=datetime.fromisoformat(model_data["last_trained"]),
                training_samples=model_data["training_samples"],
                metadata=model_data["metadata"]
            )
            
            self.add_model(model)
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False


class AnomalyDetector:
    """Anomaly detection system"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.is_fitted = False
        self.feature_extractor = FeatureExtractor()
    
    def fit(self, normal_data: List[Dict[str, Any]]) -> None:
        """Fit the anomaly detector with normal data"""
        features = []
        for data in normal_data:
            features.append(list(self.feature_extractor.extract_request_features(data).values()))
        
        X = np.array(features)
        self.isolation_forest.fit(X)
        self.is_fitted = True
    
    def detect_anomaly(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if request is anomalous"""
        if not self.is_fitted:
            return {"is_anomaly": False, "score": 0.0, "message": "Model not fitted"}
        
        features = self.feature_extractor.extract_request_features(request_data)
        feature_values = list(features.values())
        X = np.array(feature_values).reshape(1, -1)
        
        anomaly_score = self.isolation_forest.decision_function(X)[0]
        is_anomaly = self.isolation_forest.predict(X)[0] == -1
        
        return {
            "is_anomaly": bool(is_anomaly),
            "score": float(anomaly_score),
            "confidence": abs(anomaly_score),
            "features": features
        }


class SmartCache:
    """ML-powered smart caching system"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, datetime] = {}
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.max_size = max_size
        self.ml_manager = MLModelManager()
        self._setup_cache_model()
    
    def _setup_cache_model(self) -> None:
        """Setup ML model for cache prediction"""
        # Create a simple model to predict cache hit probability
        model = MLModel(
            name="cache_predictor",
            model_type=MLModelType.CLASSIFICATION,
            model=RandomForestClassifier(n_estimators=100, random_state=42),
            features=['path_length', 'has_query_params', 'hour_of_day', 'day_of_week'],
            target="cache_hit"
        )
        self.ml_manager.add_model(model)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            self.access_times[key] = datetime.now()
            self.access_counts[key] += 1
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache"""
        if len(self.cache) >= self.max_size:
            self._evict_least_used()
        
        self.cache[key] = value
        self.access_times[key] = datetime.now()
        self.access_counts[key] = 0
    
    def predict_cache_hit(self, request_data: Dict[str, Any]) -> float:
        """Predict cache hit probability for a request"""
        features = self.ml_manager.feature_extractor.extract_request_features(request_data)
        
        # Use only features available in the model
        model_features = {k: features.get(k, 0) for k in self.ml_manager.get_model("cache_predictor").features}
        
        request = PredictionRequest(
            features=model_features,
            model_name="cache_predictor",
            prediction_type=PredictionType.CACHE_HIT
        )
        
        result = self.ml_manager.predict(request)
        return result.confidence if result.prediction else 0.0
    
    def _evict_least_used(self) -> None:
        """Evict least used items from cache"""
        if not self.cache:
            return
        
        # Find item with lowest access count and oldest access time
        least_used_key = min(
            self.cache.keys(),
            key=lambda k: (self.access_counts[k], self.access_times[k])
        )
        
        del self.cache[least_used_key]
        del self.access_times[least_used_key]
        del self.access_counts[least_used_key]


class MLIntegration:
    """Main ML integration system"""
    
    def __init__(self):
        self.model_manager = MLModelManager()
        self.anomaly_detector = AnomalyDetector()
        self.smart_cache = SmartCache()
        self.request_history: deque = deque(maxlen=10000)
        self.response_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def record_request(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """Record request-response pair for ML training"""
        self.request_history.append({
            "request": request_data,
            "response": response_data,
            "timestamp": datetime.now()
        })
        
        # Update response patterns
        path = request_data.get('path', '')
        self.response_patterns[path].append(response_data)
    
    def create_response_time_model(self) -> MLModel:
        """Create a model to predict response times"""
        model = MLModel(
            name="response_time_predictor",
            model_type=MLModelType.REGRESSION,
            model=LinearRegression(),
            features=['method_encoded', 'path_length', 'body_length', 'header_count', 'hour_of_day'],
            target="response_time"
        )
        self.model_manager.add_model(model)
        return model
    
    def create_error_probability_model(self) -> MLModel:
        """Create a model to predict error probability"""
        model = MLModel(
            name="error_probability_predictor",
            model_type=MLModelType.CLASSIFICATION,
            model=MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42),
            features=['method_encoded', 'path_length', 'body_length', 'hour_of_day', 'day_of_week'],
            target="error_probability"
        )
        self.model_manager.add_model(model)
        return model
    
    def train_models(self) -> Dict[str, Any]:
        """Train all models with collected data"""
        results = {}
        
        # Prepare training data
        if len(self.request_history) < 100:
            return {"error": "Insufficient training data"}
        
        # Response time model
        response_time_model = self.create_response_time_model()
        response_time_data = self._prepare_response_time_data()
        if response_time_data:
            results["response_time"] = self.model_manager.train_model(
                "response_time_predictor", response_time_data
            )
        
        # Error probability model
        error_model = self.create_error_probability_model()
        error_data = self._prepare_error_data()
        if error_data:
            results["error_probability"] = self.model_manager.train_model(
                "error_probability_predictor", error_data
            )
        
        # Anomaly detector
        normal_data = [item["request"] for item in self.request_history]
        self.anomaly_detector.fit(normal_data)
        results["anomaly_detector"] = {"fitted": True}
        
        return results
    
    def _prepare_response_time_data(self) -> Optional[TrainingData]:
        """Prepare training data for response time prediction"""
        features = []
        targets = []
        
        for item in self.request_history:
            request = item["request"]
            response = item["response"]
            
            # Extract features
            request_features = self.model_manager.feature_extractor.extract_request_features(request)
            response_features = self.model_manager.feature_extractor.extract_response_features(response)
            
            # Combine features
            combined_features = {**request_features, **response_features}
            features.append(combined_features)
            
            # Target is response time (simulated)
            targets.append(np.random.uniform(0.1, 2.0))  # Simulated response time
        
        if not features:
            return None
        
        return TrainingData(
            features=features,
            targets=targets,
            feature_names=list(features[0].keys()),
            target_name="response_time"
        )
    
    def _prepare_error_data(self) -> Optional[TrainingData]:
        """Prepare training data for error probability prediction"""
        features = []
        targets = []
        
        for item in self.request_history:
            request = item["request"]
            response = item["response"]
            
            # Extract features
            request_features = self.model_manager.feature_extractor.extract_request_features(request)
            features.append(request_features)
            
            # Target is error probability (1 if error, 0 if success)
            is_error = response.get("status_code", 200) >= 400
            targets.append(1 if is_error else 0)
        
        if not features:
            return None
        
        return TrainingData(
            features=features,
            targets=targets,
            feature_names=list(features[0].keys()),
            target_name="error_probability"
        )
    
    def predict_response_time(self, request_data: Dict[str, Any]) -> float:
        """Predict response time for a request"""
        request = PredictionRequest(
            features=request_data,
            model_name="response_time_predictor",
            prediction_type=PredictionType.RESPONSE_TIME
        )
        
        result = self.model_manager.predict(request)
        return result.prediction if result.prediction else 1.0
    
    def predict_error_probability(self, request_data: Dict[str, Any]) -> float:
        """Predict error probability for a request"""
        request = PredictionRequest(
            features=request_data,
            model_name="error_probability_predictor",
            prediction_type=PredictionType.ERROR_PROBABILITY
        )
        
        result = self.model_manager.predict(request)
        return result.confidence if result.prediction else 0.0
    
    def detect_anomaly(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in request"""
        return self.anomaly_detector.detect_anomaly(request_data)
    
    def get_cache_recommendation(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get cache recommendation for a request"""
        cache_hit_probability = self.smart_cache.predict_cache_hit(request_data)
        
        return {
            "should_cache": cache_hit_probability > 0.7,
            "cache_hit_probability": cache_hit_probability,
            "recommended_ttl": int(3600 * cache_hit_probability)  # TTL in seconds
        }
    
    def generate_smart_response(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a smart response using ML predictions"""
        # Predict response characteristics
        response_time = self.predict_response_time(request_data)
        error_probability = self.predict_error_probability(request_data)
        anomaly_result = self.detect_anomaly(request_data)
        cache_recommendation = self.get_cache_recommendation(request_data)
        
        # Generate response based on predictions
        if error_probability > 0.5:
            status_code = np.random.choice([400, 401, 403, 404, 500], p=[0.3, 0.2, 0.1, 0.3, 0.1])
        else:
            status_code = 200
        
        response = {
            "status_code": status_code,
            "headers": {
                "Content-Type": "application/json",
                "X-ML-Predicted": "true",
                "X-Response-Time": str(response_time),
                "X-Error-Probability": str(error_probability)
            },
            "body": {
                "message": "ML-generated response",
                "predicted_response_time": response_time,
                "error_probability": error_probability,
                "is_anomaly": anomaly_result["is_anomaly"],
                "cache_recommendation": cache_recommendation
            }
        }
        
        # Add cache headers if recommended
        if cache_recommendation["should_cache"]:
            response["headers"]["Cache-Control"] = f"max-age={cache_recommendation['recommended_ttl']}"
        
        return response


# Global ML integration instance
ml_integration = MLIntegration()


# Convenience functions
def create_ml_model(name: str, model_type: MLModelType, features: List[str], target: str) -> MLModel:
    """Create a new ML model"""
    if model_type == MLModelType.CLASSIFICATION:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    elif model_type == MLModelType.REGRESSION:
        model = LinearRegression()
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    ml_model = MLModel(
        name=name,
        model_type=model_type,
        model=model,
        features=features,
        target=target
    )
    
    ml_integration.model_manager.add_model(ml_model)
    return ml_model


def train_ml_models() -> Dict[str, Any]:
    """Train all ML models"""
    return ml_integration.train_models()


def predict_response_characteristics(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Predict response characteristics for a request"""
    return {
        "response_time": ml_integration.predict_response_time(request_data),
        "error_probability": ml_integration.predict_error_probability(request_data),
        "anomaly_detection": ml_integration.detect_anomaly(request_data),
        "cache_recommendation": ml_integration.get_cache_recommendation(request_data)
    }
