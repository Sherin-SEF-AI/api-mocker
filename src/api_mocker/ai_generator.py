"""
AI-Powered Mock Generation for API-Mocker.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import logging
from contextlib import contextmanager

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

import jsonschema
from pydantic import BaseModel, Field
import jinja2

logger = logging.getLogger(__name__)

@dataclass
class GenerationRequest:
    """Request for AI-powered data generation."""
    prompt: str
    endpoint: str
    method: str = "GET"
    schema: Optional[Dict] = None
    count: int = 1
    language: str = "en"
    context: Optional[Dict] = None

@dataclass
class GenerationResponse:
    """Response from AI-powered data generation."""
    data: Any
    metadata: Dict[str, Any]
    cache_key: Optional[str] = None
    generation_time: float = 0.0

class SchemaAnalyzer:
    """Analyzes API schemas to understand data structure."""
    
    def __init__(self):
        self.faker = Faker() if FAKER_AVAILABLE else None
        
    def analyze_schema(self, schema: Dict) -> Dict[str, Any]:
        """Analyze JSON schema to understand data types and patterns."""
        analysis = {
            "types": {},
            "patterns": {},
            "constraints": {},
            "examples": {}
        }
        
        if not schema:
            return analysis
            
        self._analyze_object(schema, analysis)
        return analysis
    
    def _analyze_object(self, obj: Dict, analysis: Dict, path: str = ""):
        """Recursively analyze schema object."""
        if "type" in obj:
            current_path = path or "root"
            analysis["types"][current_path] = obj["type"]
            
            # Analyze constraints
            if "minLength" in obj or "maxLength" in obj:
                analysis["constraints"][current_path] = {
                    "minLength": obj.get("minLength"),
                    "maxLength": obj.get("maxLength")
                }
            
            # Analyze patterns
            if "pattern" in obj:
                analysis["patterns"][current_path] = obj["pattern"]
            
            # Store examples
            if "example" in obj:
                analysis["examples"][current_path] = obj["example"]
        
        # Analyze properties for objects
        if "properties" in obj:
            for prop_name, prop_schema in obj["properties"].items():
                prop_path = f"{path}.{prop_name}" if path else prop_name
                self._analyze_object(prop_schema, analysis, prop_path)
        
        # Analyze items for arrays
        if "items" in obj:
            items_path = f"{path}[items]" if path else "items"
            self._analyze_object(obj["items"], analysis, items_path)

class AIGenerator:
    """AI-powered data generator using OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self.schema_analyzer = SchemaAnalyzer()
        self.cache: Dict[str, Any] = {}
        
        if OPENAI_AVAILABLE and api_key:
            if api_key.startswith('gsk_'):
                # Groq API key
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
            else:
                # OpenAI API key
                self.client = OpenAI(api_key=api_key)
        
    def generate_data(self, request: GenerationRequest) -> GenerationResponse:
        """Generate realistic data using AI."""
        start_time = time.time()
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        if cache_key in self.cache:
            logger.info(f"Using cached data for {cache_key}")
            return GenerationResponse(
                data=self.cache[cache_key],
                metadata={"source": "cache"},
                cache_key=cache_key,
                generation_time=0.0
            )
        
        try:
            if self.client and OPENAI_AVAILABLE:
                data = self._generate_with_ai(request)
                source = "ai"
            else:
                data = self._generate_with_faker(request)
                source = "faker"
            
            # Cache the result
            self.cache[cache_key] = data
            
            generation_time = time.time() - start_time
            
            return GenerationResponse(
                data=data,
                metadata={
                    "source": source,
                    "model": self.model if source == "ai" else "faker",
                    "cache_key": cache_key
                },
                cache_key=cache_key,
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            # Fallback to Faker
            data = self._generate_with_faker(request)
            generation_time = time.time() - start_time
            
            return GenerationResponse(
                data=data,
                metadata={"source": "faker_fallback", "error": str(e)},
                generation_time=generation_time
            )
    
    def _generate_with_ai(self, request: GenerationRequest) -> Any:
        """Generate data using OpenAI API."""
        if not self.client:
            raise ValueError("OpenAI client not available")
        
        # Build the prompt
        prompt = self._build_ai_prompt(request)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert API developer. Generate realistic, diverse, and contextually appropriate mock data for API responses. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse the response
        content = response.choices[0].message.content
        try:
            # Try to extract JSON from the response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()
            
            return json.loads(json_str)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to fix common issues
            return self._fix_json_response(content)
    
    def _generate_with_faker(self, request: GenerationRequest) -> Any:
        """Generate data using Faker as fallback."""
        if not FAKER_AVAILABLE:
            raise ValueError("Faker not available")
        
        faker = Faker(request.language)
        
        # Analyze schema if available
        if request.schema:
            analysis = self.schema_analyzer.analyze_schema(request.schema)
            return self._generate_from_schema_analysis(analysis, faker, request.count)
        else:
            # Generate based on prompt keywords
            return self._generate_from_prompt(request.prompt, faker, request.count)
    
    def _build_ai_prompt(self, request: GenerationRequest) -> str:
        """Build a comprehensive prompt for AI generation."""
        prompt_parts = [
            f"Generate realistic mock data for an API endpoint: {request.endpoint}",
            f"HTTP Method: {request.method}",
            f"Number of records: {request.count}",
            f"User request: {request.prompt}"
        ]
        
        if request.schema:
            prompt_parts.append(f"JSON Schema: {json.dumps(request.schema, indent=2)}")
        
        if request.context:
            prompt_parts.append(f"Context: {json.dumps(request.context, indent=2)}")
        
        prompt_parts.extend([
            "Requirements:",
            "- Generate realistic, diverse data",
            "- Follow the schema if provided",
            "- Include edge cases and variations",
            "- Make data contextually appropriate",
            "- Return valid JSON only",
            "- If generating multiple records, return an array"
        ])
        
        return "\n\n".join(prompt_parts)
    
    def _generate_cache_key(self, request: GenerationRequest) -> str:
        """Generate a cache key for the request."""
        key_data = {
            "prompt": request.prompt,
            "endpoint": request.endpoint,
            "method": request.method,
            "count": request.count,
            "language": request.language,
            "schema_hash": hashlib.md5(json.dumps(request.schema or {}, sort_keys=True).encode()).hexdigest()[:8]
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _fix_json_response(self, content: str) -> Any:
        """Attempt to fix common JSON formatting issues."""
        # Remove markdown formatting
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Try to find JSON-like content
        import re
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, content, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Last resort: return as string
        return {"error": "Could not parse AI response", "raw_content": content}
    
    def _generate_from_schema_analysis(self, analysis: Dict, faker: Faker, count: int) -> Any:
        """Generate data based on schema analysis."""
        if count == 1:
            return self._generate_single_record(analysis, faker)
        else:
            return [self._generate_single_record(analysis, faker) for _ in range(count)]
    
    def _generate_single_record(self, analysis: Dict, faker: Faker) -> Dict:
        """Generate a single record based on schema analysis."""
        record = {}
        
        for field_path, field_type in analysis["types"].items():
            if "." in field_path:
                # Nested field
                parts = field_path.split(".")
                current = record
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = self._generate_field_value(field_type, faker)
            else:
                # Root field
                record[field_path] = self._generate_field_value(field_type, faker)
        
        return record
    
    def _generate_field_value(self, field_type: str, faker: Faker) -> Any:
        """Generate a value for a specific field type."""
        if field_type == "string":
            return faker.text(max_nb_chars=50)
        elif field_type == "integer":
            return faker.random_int(min=1, max=1000)
        elif field_type == "number":
            return faker.pyfloat(min_value=0, max_value=1000)
        elif field_type == "boolean":
            return faker.boolean()
        elif field_type == "array":
            return [faker.word() for _ in range(faker.random_int(min=1, max=5))]
        elif field_type == "object":
            return {"key": faker.word(), "value": faker.text(max_nb_chars=20)}
        else:
            return faker.word()
    
    def _generate_from_prompt(self, prompt: str, faker: Faker, count: int) -> Any:
        """Generate data based on prompt keywords."""
        prompt_lower = prompt.lower()
        
        # Detect common patterns
        if "user" in prompt_lower or "person" in prompt_lower:
            if count == 1:
                return {
                    "id": faker.uuid4(),
                    "name": faker.name(),
                    "email": faker.email(),
                    "phone": faker.phone_number(),
                    "address": faker.address(),
                    "created_at": faker.iso8601()
                }
            else:
                return [{
                    "id": faker.uuid4(),
                    "name": faker.name(),
                    "email": faker.email(),
                    "phone": faker.phone_number(),
                    "address": faker.address(),
                    "created_at": faker.iso8601()
                } for _ in range(count)]
        
        elif "product" in prompt_lower or "item" in prompt_lower:
            if count == 1:
                return {
                    "id": faker.uuid4(),
                    "name": faker.word() + " " + faker.word(),
                    "price": faker.pyfloat(min_value=1, max_value=1000),
                    "description": faker.text(max_nb_chars=100),
                    "category": faker.word(),
                    "in_stock": faker.boolean()
                }
            else:
                return [{
                    "id": faker.uuid4(),
                    "name": faker.word() + " " + faker.word(),
                    "price": faker.pyfloat(min_value=1, max_value=1000),
                    "description": faker.text(max_nb_chars=100),
                    "category": faker.word(),
                    "in_stock": faker.boolean()
                } for _ in range(count)]
        
        else:
            # Generic response
            if count == 1:
                return {
                    "id": faker.uuid4(),
                    "data": faker.text(max_nb_chars=50),
                    "timestamp": faker.iso8601(),
                    "status": "success"
                }
            else:
                return [{
                    "id": faker.uuid4(),
                    "data": faker.text(max_nb_chars=50),
                    "timestamp": faker.iso8601(),
                    "status": "success"
                } for _ in range(count)]

class TemplateEngine:
    """Template engine for dynamic response generation."""
    
    def __init__(self):
        self.jinja_env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=True
        )
    
    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template with context."""
        try:
            jinja_template = self.jinja_env.from_string(template)
            return jinja_template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template

class AIGenerationManager:
    """Manages AI-powered generation for API-Mocker."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.ai_generator = AIGenerator(api_key)
        self.template_engine = TemplateEngine()
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour
        
    def generate_mock_data(self, 
                          prompt: str,
                          endpoint: str,
                          method: str = "GET",
                          schema: Optional[Dict] = None,
                          count: int = 1,
                          language: str = "en",
                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate mock data using AI."""
        
        request = GenerationRequest(
            prompt=prompt,
            endpoint=endpoint,
            method=method,
            schema=schema,
            count=count,
            language=language,
            context=context
        )
        
        response = self.ai_generator.generate_data(request)
        
        return {
            "data": response.data,
            "metadata": response.metadata,
            "generation_time": response.generation_time,
            "cache_key": response.cache_key
        }
    
    def generate_from_schema(self, schema: Dict, count: int = 1) -> Dict[str, Any]:
        """Generate data from JSON schema."""
        return self.generate_mock_data(
            prompt="Generate data based on the provided JSON schema",
            endpoint="/schema-based",
            schema=schema,
            count=count
        )
    
    def generate_from_example(self, example: Dict, count: int = 1) -> Dict[str, Any]:
        """Generate data based on an example."""
        return self.generate_mock_data(
            prompt=f"Generate data similar to this example: {json.dumps(example)}",
            endpoint="/example-based",
            count=count
        )
    
    def clear_cache(self):
        """Clear the generation cache."""
        self.ai_generator.cache.clear()
        logger.info("AI generation cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.ai_generator.cache),
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl
        } 