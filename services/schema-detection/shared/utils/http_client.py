"""HTTP client utilities for inter-service communication."""

import httpx
import json
from typing import Optional, Dict, Any, Union
from ..models.base import BaseResponse, ErrorResponse
from .exceptions import ServiceUnavailableError, SchemaSageException


class HTTPClient:
    """HTTP client for inter-service communication."""
    
    def __init__(self, base_url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = headers or {}
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers for request."""
        headers = self.headers.copy()
        if additional_headers:
            headers.update(additional_headers)
        return headers
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[BaseResponse, ErrorResponse]:
        """Make GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._prepare_headers(headers)
        
        try:
            response = await self.client.get(url, params=params, headers=request_headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ServiceUnavailableError("http_client", str(e))
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[BaseResponse, ErrorResponse]:
        """Make POST request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._prepare_headers(headers)
        
        try:
            response = await self.client.post(
                url, 
                data=data, 
                json=json_data, 
                headers=request_headers
            )
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ServiceUnavailableError("http_client", str(e))
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[BaseResponse, ErrorResponse]:
        """Make PUT request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._prepare_headers(headers)
        
        try:
            response = await self.client.put(
                url, 
                data=data, 
                json=json_data, 
                headers=request_headers
            )
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ServiceUnavailableError("http_client", str(e))
    
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[BaseResponse, ErrorResponse]:
        """Make DELETE request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._prepare_headers(headers)
        
        try:
            response = await self.client.delete(url, headers=request_headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ServiceUnavailableError("http_client", str(e))
    
    def _handle_response(self, response: httpx.Response) -> Union[BaseResponse, ErrorResponse]:
        """Handle HTTP response."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"message": response.text}
        
        if response.is_success:
            return BaseResponse(**data)
        else:
            return ErrorResponse(
                message=data.get("message", "Request failed"),
                error_code=data.get("error_code", f"HTTP_{response.status_code}"),
                error_details=data.get("error_details", {"status_code": response.status_code})
            )
