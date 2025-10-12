"""
JWT token validation utilities
"""
from jose import jwt, JWTError
from typing import Optional
import logging
from config.settings import JWT_SECRET_KEY, JWT_ALGORITHM

logger = logging.getLogger(__name__)

async def validate_jwt_token(token: str) -> Optional[str]:
    """Validate JWT token and return user ID"""
    if not token:
        logger.warning("Empty token provided")
        return None

    try:
        # Clean token if needed
        token = token.strip()
        if token.startswith("Bearer "):
            token = token[7:]

        # Decode without verification first to check structure
        try:
            unverified_payload = jwt.get_unverified_claims(token)
            if "sub" not in unverified_payload:
                logger.warning("Token missing 'sub' claim")
                return None
        except Exception as e:
            logger.warning(f"Token structure invalid: {e}")
            return None

        # Now do full verification
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True, "verify_aud": False}
        )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token payload missing user ID")
            return None

        logger.info(f"Token validated successfully for user {user_id}")
        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected token validation error: {str(e)}")
        return None