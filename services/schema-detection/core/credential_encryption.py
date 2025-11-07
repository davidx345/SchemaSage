"""
Credential Encryption Module
Handles secure encryption and decryption of cloud provider credentials
"""

from cryptography.fernet import Fernet
import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """Handles encryption and decryption of cloud credentials"""
    
    def __init__(self):
        """Initialize encryption with key from environment"""
        encryption_key = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
        
        if not encryption_key:
            # Generate a key for development (DO NOT use in production)
            logger.warning("No CREDENTIAL_ENCRYPTION_KEY found, generating temporary key")
            encryption_key = Fernet.generate_key().decode()
            logger.warning(f"Generated key: {encryption_key}")
            logger.warning("Add this to your .env file as CREDENTIAL_ENCRYPTION_KEY")
        
        try:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption cipher: {e}")
            raise ValueError("Invalid encryption key format")
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials dictionary to string
        
        Args:
            credentials: Dictionary containing cloud provider credentials
            
        Returns:
            Encrypted string safe for database storage
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(credentials)
            
            # Encrypt
            encrypted = self.cipher.encrypt(json_str.encode())
            
            # Return as string
            return encrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """
        Decrypt encrypted credentials string
        
        Args:
            encrypted: Encrypted credentials string from database
            
        Returns:
            Dictionary containing decrypted credentials
        """
        try:
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted.encode())
            
            # Parse JSON
            credentials = json.loads(decrypted.decode())
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def rotate_key(self, old_key: str, new_key: str, encrypted_data: str) -> str:
        """
        Rotate encryption key by re-encrypting data with new key
        
        Args:
            old_key: Previous encryption key
            new_key: New encryption key
            encrypted_data: Data encrypted with old key
            
        Returns:
            Data re-encrypted with new key
        """
        try:
            # Decrypt with old key
            old_cipher = Fernet(old_key.encode())
            decrypted = old_cipher.decrypt(encrypted_data.encode())
            
            # Encrypt with new key
            new_cipher = Fernet(new_key.encode())
            re_encrypted = new_cipher.encrypt(decrypted)
            
            return re_encrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption key: {e}")
            raise ValueError(f"Key rotation failed: {str(e)}")


# Global instance
_credential_encryptor = None


def get_credential_encryptor() -> CredentialEncryption:
    """Get or create global credential encryptor instance"""
    global _credential_encryptor
    
    if _credential_encryptor is None:
        _credential_encryptor = CredentialEncryption()
    
    return _credential_encryptor


# Helper functions for easy import
def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Encrypt credentials - convenience function"""
    return get_credential_encryptor().encrypt_credentials(credentials)


def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    """Decrypt credentials - convenience function"""
    return get_credential_encryptor().decrypt_credentials(encrypted)
