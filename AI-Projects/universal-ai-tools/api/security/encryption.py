"""
Encryption service for protecting sensitive data at rest
Uses Fernet (symmetric encryption) for field-level encryption
"""

from cryptography.fernet import Fernet
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Handles encryption and decryption of sensitive data
    
    Uses Fernet (AES-128 in CBC mode) for symmetric encryption.
    Key should be stored securely in environment variable.
    """
    
    def __init__(self):
        # Try to load key from environment
        key_str = os.getenv('ATHENA_ENCRYPTION_KEY')
        
        if not key_str:
            # Generate new key for development
            key = Fernet.generate_key()
            logger.warning(f"⚠️  No ATHENA_ENCRYPTION_KEY found. Generated new key: {key.decode()}")
            logger.warning("⚠️  Set this as environment variable for production!")
            self.cipher = Fernet(key)
        else:
            # Use provided key
            key_bytes = key_str.encode() if isinstance(key_str, str) else key_str
            self.cipher = Fernet(key_bytes)
            logger.info("✅ Encryption service initialized with provided key")
    
    def encrypt(self, data: Optional[str]) -> Optional[str]:
        """
        Encrypt a string value
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if data is None or data == '':
            return data
        
        try:
            encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: Optional[str]) -> Optional[str]:
        """
        Decrypt an encrypted string value
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted plain text string, or None if input is None
        """
        if encrypted_data is None or encrypted_data == '':
            return encrypted_data
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # Return as-is if decryption fails (might be unencrypted legacy data)
            logger.warning("Returning data as-is (might be unencrypted)")
            return encrypted_data
    
    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data
            fields: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing encrypted data
            fields: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result


# Global instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
