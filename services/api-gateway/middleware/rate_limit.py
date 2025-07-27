"""
Rate limiting middleware for API Gateway
"""
import time
from typing import Dict, List
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# Rate limiting storage
request_counts: Dict[str, List[float]] = {}

def is_rate_limited(identifier: str, limit_per_minute: int = 100) -> bool:
    """Check if identifier is rate limited."""
    current_time = time.time()
    minute_ago = current_time - 60
    
    if identifier in request_counts:
        request_counts[identifier] = [t for t in request_counts[identifier] if t > minute_ago]
    else:
        request_counts[identifier] = []
    
    if len(request_counts[identifier]) >= limit_per_minute:
        return True
    
    request_counts[identifier].append(current_time)
    return False

def check_rate_limit(client_ip: str, user_id: str = None, limit_per_minute: int = 100):
    """Check rate limit and raise exception if exceeded."""
    identifier = user_id if user_id else client_ip
    
    if is_rate_limited(identifier, limit_per_minute):
        logger.warning(f"Rate limit exceeded for {identifier}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

def get_rate_limit_info(identifier: str) -> Dict[str, int]:
    """Get current rate limit status for identifier."""
    current_time = time.time()
    minute_ago = current_time - 60
    
    if identifier in request_counts:
        request_counts[identifier] = [t for t in request_counts[identifier] if t > minute_ago]
        current_requests = len(request_counts[identifier])
    else:
        current_requests = 0
    
    return {
        "current_requests": current_requests,
        "limit": 100,
        "remaining": max(0, 100 - current_requests),
        "reset_time": int(current_time + 60)
    }
