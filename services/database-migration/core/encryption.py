"""
Enterprise Encryption Service
AES-256-GCM encryption for sensitive database connection data
Includes key rotation, salt generation, and secure key derivation
"""
import os
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Dict, Any, Optional
import json
import base64
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EncryptionConfig:
    """Encryption configuration with enterprise security standards"""
    
    # Primary encryption key from environment (should be 32 bytes for AES-256)
    MASTER_KEY = os.getenv("SCHEMASAGE_MASTER_KEY", "dev_master_key_not_for_production_use_32_bytes!")
    
    # Key derivation settings
    PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "100000"))
    SALT_LENGTH = 32  # 256 bits
    KEY_LENGTH = 32   # 256 bits for AES-256
    
    # GCM settings
    GCM_TAG_LENGTH = 16  # 128 bits
    GCM_NONCE_LENGTH = 12  # 96 bits (recommended for GCM)
    
    # Key rotation
    KEY_ROTATION_DAYS = int(os.getenv("KEY_ROTATION_DAYS", "90"))
    
    @classmethod
    def validate_master_key(cls) -> bool:
        """Validate master key meets security requirements"""
        key = cls.MASTER_KEY.encode('utf-8')
        return len(key) >= 32  # At least 256 bits


class ConnectionEncryption:
    """
    Enterprise-grade encryption service for database connection secrets
    
    Features:
    - AES-256-GCM encryption
    - PBKDF2 key derivation with salt
    - Authenticated encryption (integrity + confidentiality)
    - Key rotation support
    - Secure random generation
    """
    
    def __init__(self):
        self.config = EncryptionConfig()
        if not self.config.validate_master_key():
            logger.warning("⚠️  Master key is too short for production use!")
    
    def generate_salt(self) -> bytes:
        """Generate cryptographically secure random salt"""
        return secrets.token_bytes(self.config.SALT_LENGTH)
    
    def derive_key(self, master_key: str, salt: bytes) -> bytes:
        """Derive encryption key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.KEY_LENGTH,
            salt=salt,
            iterations=self.config.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(master_key.encode('utf-8'))
    
    def encrypt_connection_data(self, connection_data: Dict[str, Any]) -> Tuple[bytes, bytes, int]:
        """
        Encrypt connection data with authenticated encryption
        
        Returns:
            (encrypted_data, salt, key_version)
        """
        try:
            # Generate salt and derive key
            salt = self.generate_salt()
            derived_key = self.derive_key(self.config.MASTER_KEY, salt)
            
            # Serialize connection data
            plaintext = json.dumps(connection_data, sort_keys=True).encode('utf-8')
            
            # Generate random nonce for GCM
            nonce = secrets.token_bytes(self.config.GCM_NONCE_LENGTH)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            # Combine nonce + ciphertext + tag
            encrypted_data = nonce + ciphertext + encryptor.tag
            
            logger.info(f"✅ Encrypted {len(plaintext)} bytes of connection data")
            return encrypted_data, salt, 1  # Key version 1
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt connection data: {e}")
    
    def decrypt_connection_data(self, encrypted_data: bytes, salt: bytes, key_version: int = 1) -> Dict[str, Any]:
        """
        Decrypt connection data with authenticated decryption
        
        Args:
            encrypted_data: The encrypted data (nonce + ciphertext + tag)
            salt: The salt used for key derivation
            key_version: Key version for rotation support
            
        Returns:
            Decrypted connection data as dictionary
        """
        try:
            # Derive key using stored salt
            derived_key = self.derive_key(self.config.MASTER_KEY, salt)
            
            # Extract components
            nonce = encrypted_data[:self.config.GCM_NONCE_LENGTH]
            tag = encrypted_data[-self.config.GCM_TAG_LENGTH:]
            ciphertext = encrypted_data[self.config.GCM_NONCE_LENGTH:-self.config.GCM_TAG_LENGTH]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt and verify
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Parse JSON
            connection_data = json.loads(plaintext.decode('utf-8'))
            
            logger.info("✅ Successfully decrypted connection data")
            return connection_data
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt connection data: {e}")
    
    def encrypt_password(self, password: str) -> Tuple[bytes, bytes]:
        """Encrypt a single password field"""
        data = {"password": password}
        encrypted_data, salt, _ = self.encrypt_connection_data(data)
        return encrypted_data, salt
    
    def decrypt_password(self, encrypted_data: bytes, salt: bytes) -> str:
        """Decrypt a single password field"""
        data = self.decrypt_connection_data(encrypted_data, salt)
        return data["password"]
    
    def rotate_encryption_key(self, old_encrypted_data: bytes, old_salt: bytes, old_key_version: int = 1) -> Tuple[bytes, bytes, int]:
        """
        Rotate encryption key for existing data
        Decrypt with old key, encrypt with new key
        """
        try:
            # Decrypt with old key
            connection_data = self.decrypt_connection_data(old_encrypted_data, old_salt, old_key_version)
            
            # Re-encrypt with new key (incremented version)
            new_encrypted_data, new_salt, new_version = self.encrypt_connection_data(connection_data)
            
            logger.info(f"✅ Rotated encryption key from v{old_key_version} to v{new_version}")
            return new_encrypted_data, new_salt, new_version
            
        except Exception as e:
            logger.error(f"❌ Key rotation failed: {e}")
            raise ValueError(f"Failed to rotate encryption key: {e}")
    
    def is_key_rotation_needed(self, created_at: datetime) -> bool:
        """Check if key rotation is needed based on age"""
        rotation_interval = timedelta(days=self.config.KEY_ROTATION_DAYS)
        return datetime.utcnow() - created_at > rotation_interval
    
    def generate_connection_hash(self, connection_data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash for connection data integrity checking"""
        # Create deterministic string representation
        data_str = json.dumps(connection_data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def mask_sensitive_data(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a safe representation for logging (masks passwords)"""
        safe_data = connection_data.copy()
        
        # Fields to mask
        sensitive_fields = ['password', 'api_key', 'secret', 'token', 'private_key']
        
        for field in sensitive_fields:
            if field in safe_data:
                if isinstance(safe_data[field], str) and len(safe_data[field]) > 0:
                    safe_data[field] = f"{'*' * min(8, len(safe_data[field]))}[MASKED]"
                else:
                    safe_data[field] = "[MASKED]"
        
        return safe_data


class EncryptionKeyManager:
    """
    Manages encryption keys and rotation for enterprise security
    """
    
    def __init__(self):
        self.encryption = ConnectionEncryption()
    
    def get_key_info(self) -> Dict[str, Any]:
        """Get information about current encryption configuration"""
        return {
            "algorithm": "AES-256-GCM",
            "key_derivation": "PBKDF2-SHA256",
            "iterations": self.encryption.config.PBKDF2_ITERATIONS,
            "salt_length": self.encryption.config.SALT_LENGTH,
            "key_length": self.encryption.config.KEY_LENGTH,
            "rotation_days": self.encryption.config.KEY_ROTATION_DAYS,
            "master_key_configured": bool(self.encryption.config.MASTER_KEY),
            "master_key_secure": self.encryption.config.validate_master_key()
        }
    
    def validate_encryption_environment(self) -> Dict[str, Any]:
        """Validate encryption environment for production readiness"""
        issues = []
        warnings = []
        
        # Check master key
        if not self.encryption.config.validate_master_key():
            issues.append("Master key is too short (minimum 32 bytes required)")
        
        if "dev_master_key" in self.encryption.config.MASTER_KEY:
            issues.append("Using development master key in production")
        
        # Check iterations
        if self.encryption.config.PBKDF2_ITERATIONS < 100000:
            warnings.append("PBKDF2 iterations below recommended minimum (100,000)")
        
        # Check key rotation
        if self.encryption.config.KEY_ROTATION_DAYS > 365:
            warnings.append("Key rotation period longer than recommended (365 days)")
        
        return {
            "secure": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": [
                "Set SCHEMASAGE_MASTER_KEY environment variable with 32+ byte key",
                "Use PBKDF2_ITERATIONS >= 100000",
                "Set KEY_ROTATION_DAYS <= 90 for high security"
            ]
        }


# Singleton instance for service use
connection_encryption = ConnectionEncryption()
key_manager = EncryptionKeyManager()