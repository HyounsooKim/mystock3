"""
Azure Key Vault integration for secure secret management.
Provides automatic secret rotation and centralized configuration.
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Azure Key Vault SDK (optional dependency)
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    KEYVAULT_AVAILABLE = True
except ImportError:
    KEYVAULT_AVAILABLE = False
    DefaultAzureCredential = None
    SecretClient = None


class KeyVaultManager:
    """
    Manage secrets stored in Azure Key Vault.
    
    Features:
    - Automatic secret retrieval
    - Credential caching
    - Fallback to environment variables
    - Secret rotation support
    """
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Initialize Key Vault manager.
        
        Args:
            vault_url: Azure Key Vault URL (e.g., https://myvault.vault.azure.net/)
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self.enabled = KEYVAULT_AVAILABLE and bool(self.vault_url)
        self.client: Optional[SecretClient] = None
        self.secret_cache: Dict[str, tuple] = {}  # {name: (value, expiry)}
        self.cache_ttl = timedelta(minutes=15)  # Cache secrets for 15 minutes
        
        if self.enabled:
            self._initialize_client()
        else:
            if not KEYVAULT_AVAILABLE:
                logger.warning(
                    "Azure Key Vault SDK not installed. "
                    "Install with: pip install azure-identity azure-keyvault-secrets"
                )
            elif not self.vault_url:
                logger.warning(
                    "AZURE_KEY_VAULT_URL not configured. "
                    "Falling back to environment variables."
                )
    
    def _initialize_client(self):
        """Initialize Azure Key Vault client with managed identity."""
        if not self.enabled:
            return
        
        try:
            # Use DefaultAzureCredential for managed identity support
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            logger.info(f"Azure Key Vault client initialized: {self.vault_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            self.enabled = False
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret from Key Vault or environment variable.
        
        Args:
            secret_name: Name of the secret in Key Vault
            fallback_env_var: Environment variable to use if Key Vault unavailable
        
        Returns:
            Secret value or None if not found
        """
        # Check cache first
        if secret_name in self.secret_cache:
            value, expiry = self.secret_cache[secret_name]
            if datetime.now() < expiry:
                logger.debug(f"Using cached secret: {secret_name}")
                return value
            else:
                # Cache expired
                del self.secret_cache[secret_name]
        
        # Try Key Vault
        if self.enabled and self.client:
            try:
                logger.info(f"Retrieving secret from Key Vault: {secret_name}")
                secret = self.client.get_secret(secret_name)
                value = secret.value
                
                # Cache the secret
                expiry = datetime.now() + self.cache_ttl
                self.secret_cache[secret_name] = (value, expiry)
                
                logger.info(f"Successfully retrieved secret: {secret_name}")
                return value
            except Exception as e:
                logger.error(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            value = os.getenv(fallback_env_var)
            if value:
                logger.info(f"Using environment variable: {fallback_env_var}")
                return value
            else:
                logger.warning(f"Secret not found: {secret_name} (env: {fallback_env_var})")
        
        return None
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store or update a secret in Key Vault.
        
        Args:
            secret_name: Name of the secret
            secret_value: Secret value to store
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.client:
            logger.error("Key Vault not available for setting secrets")
            return False
        
        try:
            logger.info(f"Setting secret in Key Vault: {secret_name}")
            self.client.set_secret(secret_name, secret_value)
            
            # Invalidate cache
            if secret_name in self.secret_cache:
                del self.secret_cache[secret_name]
            
            logger.info(f"Successfully set secret: {secret_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{secret_name}': {e}")
            return False
    
    def rotate_secret(self, secret_name: str, new_value: str) -> bool:
        """
        Rotate a secret (set new value).
        
        Args:
            secret_name: Name of the secret to rotate
            new_value: New secret value
        
        Returns:
            True if successful
        """
        logger.info(f"Rotating secret: {secret_name}")
        return self.set_secret(secret_name, new_value)
    
    def clear_cache(self):
        """Clear the secret cache."""
        self.secret_cache.clear()
        logger.info("Secret cache cleared")


# Global Key Vault manager instance
_keyvault_manager: Optional[KeyVaultManager] = None


def get_keyvault_manager(vault_url: Optional[str] = None) -> KeyVaultManager:
    """
    Get or create the global Key Vault manager instance.
    
    Args:
        vault_url: Azure Key Vault URL (optional, uses env var if not provided)
    
    Returns:
        KeyVaultManager instance
    """
    global _keyvault_manager
    
    if _keyvault_manager is None:
        _keyvault_manager = KeyVaultManager(vault_url)
    
    return _keyvault_manager


def get_secret_from_keyvault(
    secret_name: str,
    fallback_env_var: Optional[str] = None,
    vault_url: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to get a secret from Key Vault.
    
    Args:
        secret_name: Name of the secret in Key Vault
        fallback_env_var: Environment variable to use as fallback
        vault_url: Key Vault URL (optional)
    
    Returns:
        Secret value or None
    """
    manager = get_keyvault_manager(vault_url)
    return manager.get_secret(secret_name, fallback_env_var)


# Secret name mappings for common configuration
SECRET_MAPPINGS = {
    "cosmos_key": ("cosmos-db-key", "MYSTOCK3_COSMOS_KEY"),
    "jwt_secret": ("jwt-secret-key", "MYSTOCK3_SECRET_KEY"),
    "alpha_vantage_key": ("alpha-vantage-api-key", "MYSTOCK3_ALPHA_VANTAGE_API_KEY"),
    "app_insights_connection": ("app-insights-connection", "APPLICATIONINSIGHTS_CONNECTION_STRING"),
}


def load_config_from_keyvault() -> Dict[str, str]:
    """
    Load all application configuration from Key Vault.
    
    Returns:
        Dictionary of configuration values
    """
    manager = get_keyvault_manager()
    config = {}
    
    for config_key, (secret_name, env_var) in SECRET_MAPPINGS.items():
        value = manager.get_secret(secret_name, env_var)
        if value:
            config[config_key] = value
        else:
            logger.warning(f"Configuration missing: {config_key}")
    
    logger.info(f"Loaded {len(config)} configuration values from Key Vault/environment")
    return config
