"""
API integration implementations
"""
import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Union
import aiohttp
import requests
from urllib.parse import urljoin, urlparse

from .base import BaseIntegration, IntegrationConfig, IntegrationType, AuthenticationType

logger = logging.getLogger(__name__)

class APIIntegration(BaseIntegration):
    """Integration for REST APIs"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.settings.get("base_url", "")
        self.timeout = config.settings.get("timeout", 30)
    
    async def connect(self) -> bool:
        """Establish API connection session"""
        try:
            # Create session with appropriate authentication
            headers = await self._get_auth_headers()
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            
            # Test connection with a simple request
            test_result = await self.test_connection()
            if test_result["success"]:
                self.is_connected = True
                logger.info(f"Connected to API: {self.config.name}")
                return True
            else:
                await self.disconnect()
                return False
            
        except Exception as e:
            logger.error(f"Failed to connect to API {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close API session"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        start_time = time.time()
        
        try:
            if not self.session:
                await self.connect()
            
            # Use custom health endpoint or root endpoint
            health_endpoint = self.config.settings.get("health_endpoint", "/health")
            test_url = urljoin(self.base_url, health_endpoint)
            
            async with self.session.get(test_url) as response:
                response_time = time.time() - start_time
                
                if response.status < 400:
                    self.update_metrics(True, response_time)
                    
                    return {
                        "success": True,
                        "message": f"API connection successful (status: {response.status})",
                        "response_time": response_time,
                        "status_code": response.status,
                        "url": test_url
                    }
                else:
                    self.update_metrics(False, response_time)
                    
                    return {
                        "success": False,
                        "message": f"API returned error status: {response.status}",
                        "response_time": response_time,
                        "status_code": response.status,
                        "url": test_url
                    }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"API connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        try:
            if not self.session:
                await self.connect()
            
            url = urljoin(self.base_url, endpoint)
            
            # Merge headers
            request_headers = {}
            if headers:
                request_headers.update(headers)
            
            kwargs = {
                'url': url,
                'headers': request_headers
            }
            
            if params:
                kwargs['params'] = params
            
            if data:
                if isinstance(data, dict):
                    kwargs['json'] = data
                else:
                    kwargs['data'] = data
            
            async with self.session.request(method.upper(), **kwargs) as response:
                response_text = await response.text()
                
                try:
                    response_data = await response.json()
                except:
                    response_data = response_text
                
                return {
                    "success": response.status < 400,
                    "status_code": response.status,
                    "data": response_data,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
                
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "data": None
            }
    
    async def get_schema_info(self) -> Optional[Dict[str, Any]]:
        """Get API schema information (OpenAPI/Swagger)"""
        try:
            # Try common schema endpoints
            schema_endpoints = [
                "/swagger.json",
                "/openapi.json",
                "/api-docs",
                "/docs.json",
                self.config.settings.get("schema_endpoint", "")
            ]
            
            for endpoint in schema_endpoints:
                if not endpoint:
                    continue
                
                result = await self.make_request("GET", endpoint)
                if result["success"] and result["data"]:
                    return {
                        "schema_type": self._detect_schema_type(result["data"]),
                        "schema_data": result["data"],
                        "endpoint": endpoint
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get API schema: {str(e)}")
            return None
    
    async def discover_endpoints(self) -> List[Dict[str, Any]]:
        """Discover available API endpoints"""
        try:
            schema_info = await self.get_schema_info()
            
            if schema_info and schema_info["schema_data"]:
                return self._extract_endpoints_from_schema(schema_info["schema_data"])
            
            # Fallback: try common endpoints
            common_endpoints = [
                "/",
                "/api",
                "/v1",
                "/health",
                "/status",
                "/info"
            ]
            
            discovered = []
            for endpoint in common_endpoints:
                result = await self.make_request("GET", endpoint)
                if result["success"]:
                    discovered.append({
                        "path": endpoint,
                        "method": "GET",
                        "status": result["status_code"],
                        "description": f"Endpoint returns {result['status_code']}"
                    })
            
            return discovered
            
        except Exception as e:
            logger.error(f"Failed to discover API endpoints: {str(e)}")
            return []
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth type"""
        headers = {}
        creds = self.config.credentials.credentials
        
        if self.config.credentials.auth_type == AuthenticationType.API_KEY:
            api_key = creds.get("api_key")
            key_header = self.config.settings.get("api_key_header", "X-API-Key")
            headers[key_header] = api_key
            
        elif self.config.credentials.auth_type == AuthenticationType.BEARER_TOKEN:
            token = creds.get("token")
            headers["Authorization"] = f"Bearer {token}"
            
        elif self.config.credentials.auth_type == AuthenticationType.BASIC_AUTH:
            import base64
            username = creds.get("username")
            password = creds.get("password")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
            
        elif self.config.credentials.auth_type == AuthenticationType.OAUTH2:
            # For OAuth2, we might need to refresh token
            token = await self._get_oauth_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        # Add custom headers
        custom_headers = self.config.settings.get("custom_headers", {})
        headers.update(custom_headers)
        
        return headers
    
    async def _get_oauth_token(self) -> Optional[str]:
        """Get OAuth2 token"""
        try:
            creds = self.config.credentials.credentials
            
            token_url = creds.get("token_url")
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")
            
            if not all([token_url, client_id, client_secret]):
                return None
            
            # Use client credentials flow
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            # Add scope if provided
            scope = creds.get("scope")
            if scope:
                data["scope"] = scope
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return token_data.get("access_token")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get OAuth token: {str(e)}")
            return None
    
    def _detect_schema_type(self, schema_data: Dict) -> str:
        """Detect schema type (OpenAPI, Swagger, etc.)"""
        if isinstance(schema_data, dict):
            if "openapi" in schema_data:
                return "openapi"
            elif "swagger" in schema_data:
                return "swagger"
            elif "paths" in schema_data:
                return "api_schema"
        
        return "unknown"
    
    def _extract_endpoints_from_schema(self, schema_data: Dict) -> List[Dict[str, Any]]:
        """Extract endpoints from API schema"""
        endpoints = []
        
        try:
            paths = schema_data.get("paths", {})
            
            for path, path_data in paths.items():
                if not isinstance(path_data, dict):
                    continue
                
                for method, method_data in path_data.items():
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        endpoint = {
                            "path": path,
                            "method": method.upper(),
                            "summary": method_data.get("summary", ""),
                            "description": method_data.get("description", ""),
                            "parameters": method_data.get("parameters", []),
                            "responses": method_data.get("responses", {})
                        }
                        endpoints.append(endpoint)
            
        except Exception as e:
            logger.error(f"Failed to extract endpoints from schema: {str(e)}")
        
        return endpoints

class WebhookIntegration(APIIntegration):
    """Integration for webhook endpoints"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.webhook_url = config.settings.get("webhook_url", "")
    
    async def send_webhook(self, data: Dict[str, Any], event_type: str = "generic") -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            # Prepare webhook payload
            payload = {
                "event_type": event_type,
                "timestamp": time.time(),
                "data": data,
                "source": self.config.name
            }
            
            # Add webhook signature if secret is provided
            headers = {}
            webhook_secret = self.config.credentials.credentials.get("webhook_secret")
            if webhook_secret:
                headers["X-Webhook-Signature"] = self._generate_webhook_signature(payload, webhook_secret)
            
            result = await self.make_request(
                "POST",
                self.webhook_url,
                data=payload,
                headers=headers
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_webhook_signature(self, payload: Dict, secret: str) -> str:
        """Generate webhook signature for payload verification"""
        import hmac
        import hashlib
        
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"

class GraphQLIntegration(BaseIntegration):
    """Integration for GraphQL APIs"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.endpoint = config.settings.get("endpoint", "")
    
    async def connect(self) -> bool:
        """Establish GraphQL connection"""
        try:
            headers = await self._get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            
            # Test with introspection query
            test_result = await self.test_connection()
            if test_result["success"]:
                self.is_connected = True
                logger.info(f"Connected to GraphQL API: {self.config.name}")
                return True
            else:
                await self.disconnect()
                return False
            
        except Exception as e:
            logger.error(f"Failed to connect to GraphQL API {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close GraphQL session"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test GraphQL connection with introspection"""
        start_time = time.time()
        
        try:
            if not self.session:
                await self.connect()
            
            # Simple introspection query
            query = """
            query {
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """
            
            result = await self.execute_query(query)
            response_time = time.time() - start_time
            
            if result["success"]:
                self.update_metrics(True, response_time)
                return {
                    "success": True,
                    "message": "GraphQL connection successful",
                    "response_time": response_time,
                    "schema_info": result["data"]
                }
            else:
                self.update_metrics(False, response_time)
                return {
                    "success": False,
                    "message": f"GraphQL connection failed: {result.get('error', 'Unknown error')}",
                    "response_time": response_time,
                    "error": result.get("error")
                }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"GraphQL connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GraphQL query"""
        try:
            if not self.session:
                await self.connect()
            
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            
            async with self.session.post(self.endpoint, json=payload) as response:
                response_data = await response.json()
                
                if response.status < 400 and "errors" not in response_data:
                    return {
                        "success": True,
                        "data": response_data.get("data"),
                        "extensions": response_data.get("extensions")
                    }
                else:
                    return {
                        "success": False,
                        "errors": response_data.get("errors", []),
                        "data": response_data.get("data")
                    }
                    
        except Exception as e:
            logger.error(f"GraphQL query failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get GraphQL schema via introspection"""
        try:
            introspection_query = """
            query IntrospectionQuery {
                __schema {
                    queryType { name }
                    mutationType { name }
                    subscriptionType { name }
                    types {
                        ...FullType
                    }
                    directives {
                        name
                        description
                        locations
                        args {
                            ...InputValue
                        }
                    }
                }
            }
            
            fragment FullType on __Type {
                kind
                name
                description
                fields(includeDeprecated: true) {
                    name
                    description
                    args {
                        ...InputValue
                    }
                    type {
                        ...TypeRef
                    }
                    isDeprecated
                    deprecationReason
                }
                inputFields {
                    ...InputValue
                }
                interfaces {
                    ...TypeRef
                }
                enumValues(includeDeprecated: true) {
                    name
                    description
                    isDeprecated
                    deprecationReason
                }
                possibleTypes {
                    ...TypeRef
                }
            }
            
            fragment InputValue on __InputValue {
                name
                description
                type { ...TypeRef }
                defaultValue
            }
            
            fragment TypeRef on __Type {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                                ofType {
                                    kind
                                    name
                                    ofType {
                                        kind
                                        name
                                        ofType {
                                            kind
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            result = await self.execute_query(introspection_query)
            
            if result["success"]:
                return result["data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get GraphQL schema: {str(e)}")
            return None
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GraphQL"""
        headers = {}
        creds = self.config.credentials.credentials
        
        if self.config.credentials.auth_type == AuthenticationType.API_KEY:
            api_key = creds.get("api_key")
            key_header = self.config.settings.get("api_key_header", "Authorization")
            headers[key_header] = f"Bearer {api_key}"
            
        elif self.config.credentials.auth_type == AuthenticationType.BEARER_TOKEN:
            token = creds.get("token")
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
