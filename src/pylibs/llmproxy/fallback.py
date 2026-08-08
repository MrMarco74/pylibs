import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def set_fallback_mode(enabled: bool, proxy_admin_url: str = "http://localhost:11435/admin/fallback", auth_token: Optional[str] = None) -> bool:
    """
    Toggles the fallback mode on llmproxy.
    """
    try:
        headers = {}
        if auth_token:
            headers["X-Admin-Token"] = auth_token
            
        # Get the current configuration
        r_get = requests.get(proxy_admin_url, headers=headers, timeout=5)
        r_get.raise_for_status()
        
        data = r_get.json()
        if data.get("enabled") == enabled:
            return True # Already in the desired state
            
        data["enabled"] = enabled
        
        # Save the new configuration
        r_post = requests.post(proxy_admin_url, json=data, headers=headers, timeout=5)
        r_post.raise_for_status()
        
        return r_post.json().get("ok", False)
    except Exception as e:
        logger.error(f"Failed to set fallback mode to {enabled}: {e}")
        return False
