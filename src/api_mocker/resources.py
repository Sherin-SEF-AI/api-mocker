from typing import Dict, Any, List, Optional
import math
from .core import CoreEngine

class ResourceHandler:
    """
    Generic handler for stateful REST resources.
    Uses CoreEngine's StateManager for persistence.
    """
    
    def __init__(self, resource_name: str, id_field: str = "id"):
        self.resource_name = resource_name
        self.id_field = id_field

    def _get_collection(self, engine: CoreEngine) -> List[Dict]:
        """Get the full collection from state manager."""
        collection = engine.state_manager.get_data(self.resource_name)
        if collection is None:
            collection = []
            engine.state_manager.set_data(self.resource_name, collection)
        return collection

    def _save_collection(self, engine: CoreEngine, collection: List[Dict]):
        """Save the collection to state manager."""
        engine.state_manager.set_data(self.resource_name, collection)

    def list(self, path: str, method: str, headers: Dict, body: Any, engine: CoreEngine, query_params: Dict = None) -> Dict:
        """
        Handle GET /resource
        Supports: search (q=), filtering (?field=value), pagination (page, limit), sorting (sort)
        """
        collection = self._get_collection(engine)
        query_params = query_params or {}
        
        # 1. Filtering & Search
        filtered = []
        search_query = query_params.get('q')
        
        for item in collection:
            matches = True
            
            # Simple Filter Matching
            for key, value in query_params.items():
                if key in ['page', 'limit', 'sort', 'q']:
                    continue
                if str(item.get(key, '')) != value:
                    matches = False
                    break
            
            # Search Query (naive text match across all string fields)
            if matches and search_query:
                text_match = False
                for v in item.values():
                    if isinstance(v, str) and search_query.lower() in v.lower():
                        text_match = True
                        break
                if not text_match:
                    matches = False
            
            if matches:
                filtered.append(item)
        
        # 2. Sorting
        sort_param = query_params.get('sort')
        if sort_param:
            reverse = False
            if sort_param.endswith('_desc'):
                key = sort_param[:-5]
                reverse = True
            elif sort_param.endswith('_asc'):
                key = sort_param[:-4]
            else:
                key = sort_param
            
            # Basic sort ability
            filtered.sort(key=lambda x: str(x.get(key, '')), reverse=reverse)

        # 3. Pagination
        page = int(query_params.get('page', 1))
        limit = int(query_params.get('limit', 10))
        total = len(filtered)
        total_pages = math.ceil(total / limit)
        
        start = (page - 1) * limit
        end = start + limit
        paginated_items = filtered[start:end]
        
        return {
            "status_code": 200,
            "body": {
                "data": paginated_items,
                "meta": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages
                }
            }
        }

    def create(self, path: str, method: str, headers: Dict, body: Any, engine: CoreEngine, query_params: Dict = None) -> Dict:
        """Handle POST /resource"""
        collection = self._get_collection(engine)
        
        new_item = body if isinstance(body, dict) else {}
        
        # Auto-generate ID if missing
        if self.id_field not in new_item:
            new_id = engine.state_manager.get_next_id(self.resource_name)
            new_item[self.id_field] = str(new_id) # Using string IDs for consistency
        
        import time
        new_item['created_at'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        collection.append(new_item)
        self._save_collection(engine, collection)
        
        return {
            "status_code": 201,
            "body": new_item
        }

    def get(self, path: str, method: str, headers: Dict, body: Any, engine: CoreEngine, query_params: Dict = None) -> Dict:
        """Handle GET /resource/{id}"""
        # We need to extract ID from the path.
        # Since we don't have direct access to resolved path params here easily without hacky parsing of 'path',
        # we rely on the router having done it.
        # Caveat: CoreEngine doesn't pass path_params.
        # Workaround: Re-parse the ID from the end of the path.
        # Assumption: standard REST path /resource/{id}
        
        # Try to get from router params first if I updated CoreEngine? I didn't update CoreEngine to pass path_params.
        # Let's just grab the last segment.
        resource_id = path.rstrip('/').split('/')[-1]
        
        collection = self._get_collection(engine)
        for item in collection:
            if str(item.get(self.id_field)) == resource_id:
                return {"status_code": 200, "body": item}
        
        return {"status_code": 404, "body": {"error": f"{self.resource_name} not found"}}

    def update(self, path: str, method: str, headers: Dict, body: Any, engine: CoreEngine, query_params: Dict = None) -> Dict:
        """Handle PUT/PATCH /resource/{id}"""
        resource_id = path.rstrip('/').split('/')[-1]
        collection = self._get_collection(engine)
        
        for i, item in enumerate(collection):
            if str(item.get(self.id_field)) == resource_id:
                # Merge updates
                updated_item = item.copy()
                if isinstance(body, dict):
                    updated_item.update(body)
                
                # Protect ID ?? Usually yes, but this is a mock.
                updated_item[self.id_field] = item[self.id_field] 
                
                collection[i] = updated_item
                self._save_collection(engine, collection)
                return {"status_code": 200, "body": updated_item}
                
        return {"status_code": 404, "body": {"error": f"{self.resource_name} not found"}}

    def delete(self, path: str, method: str, headers: Dict, body: Any, engine: CoreEngine, query_params: Dict = None) -> Dict:
        """Handle DELETE /resource/{id}"""
        resource_id = path.rstrip('/').split('/')[-1]
        collection = self._get_collection(engine)
        
        initial_len = len(collection)
        collection = [item for item in collection if str(item.get(self.id_field)) != resource_id]
        
        if len(collection) < initial_len:
            self._save_collection(engine, collection)
            return {"status_code": 204, "body": None}
            
        return {"status_code": 404, "body": {"error": f"{self.resource_name} not found"}}
