#!/usr/bin/env python3
"""
Smartproxy/Decodo Integration Utilities

Provides secure proxy configuration and request routing for the AI image
generation pipeline, enhancing reliability and geographic distribution.
"""

import os
import requests
from typing import Dict, Optional
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, rely on system environment variables
    pass


class SmartproxyConfig:
    """Configuration manager for Smartproxy/Decodo service."""
    
    def __init__(self):
        """Initialize with credentials from environment variables."""
        self.username = os.getenv('SMARTPROXY_USERNAME')
        self.password = os.getenv('SMARTPROXY_PASSWORD')
        self.auth_token = os.getenv('SMARTPROXY_AUTH_TOKEN')
        
        if not all([self.username, self.password, self.auth_token]):
            raise ValueError(
                "Missing Smartproxy credentials. Please set SMARTPROXY_USERNAME, "
                "SMARTPROXY_PASSWORD, and SMARTPROXY_AUTH_TOKEN environment variables."
            )
    
    def get_proxy_config(self, endpoint: str = "datacenter") -> Dict[str, str]:
        """Get proxy configuration for requests.
        
        Args:
            endpoint: Proxy endpoint type ('datacenter', 'residential', etc.)
            
        Returns:
            Dictionary with proxy configuration for requests library
        """
        proxy_url = f"http://{self.username}:{self.password}@gate.smartproxy.com:10000"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for direct API calls.
        
        Returns:
            Dictionary with authentication headers
        """
        return {
            'Authorization': f'Basic {self.auth_token}',
            'User-Agent': 'AI-Image-Generator-Pipeline/1.0'
        }
    
    def test_connection(self) -> bool:
        """Test proxy connection and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            proxies = self.get_proxy_config()
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Proxy connection test failed: {e}")
            return False


def make_proxied_request(url: str, method: str = 'GET', **kwargs) -> requests.Response:
    """Make HTTP request through Smartproxy service.
    
    Args:
        url: Target URL for the request
        method: HTTP method ('GET', 'POST', etc.)
        **kwargs: Additional arguments passed to requests
        
    Returns:
        Response object from the proxied request
        
    Raises:
        ValueError: If Smartproxy credentials are not configured
        requests.RequestException: If request fails
    """
    config = SmartproxyConfig()
    
    # Add proxy configuration to kwargs
    kwargs.setdefault('proxies', config.get_proxy_config())
    kwargs.setdefault('headers', {}).update(config.get_auth_headers())
    kwargs.setdefault('timeout', 30)
    
    # Make the request
    response = requests.request(method, url, **kwargs)
    return response


if __name__ == '__main__':
    """Test Smartproxy configuration when run directly."""
    try:
        config = SmartproxyConfig()
        print("✓ Smartproxy credentials loaded successfully")
        
        print("Testing proxy connection...")
        if config.test_connection():
            print("✓ Proxy connection test successful")
            
            # Test getting IP through proxy
            response = make_proxied_request('http://httpbin.org/ip')
            ip_info = response.json()
            print(f"✓ Proxy IP: {ip_info.get('origin', 'Unknown')}")
        else:
            print("✗ Proxy connection test failed")
            
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease ensure your .env file contains:")
        print("SMARTPROXY_USERNAME=your_username")
        print("SMARTPROXY_PASSWORD=your_password") 
        print("SMARTPROXY_AUTH_TOKEN=your_auth_token")

