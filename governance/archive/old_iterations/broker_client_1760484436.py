#!/usr/bin/env python3
"""
Assistant Broker Python Client
Minimal, production-ready client for broker API
"""

import os
import requests
from typing import Optional, List, Dict, Any


class BrokerClient:
    """Client for Assistant Broker API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080", token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        
        # Get token from env or file
        if token:
            self.token = token
        elif os.environ.get("ASSISTANT_BROKER_TOKEN"):
            self.token = os.environ["ASSISTANT_BROKER_TOKEN"]
        else:
            token_path = os.path.expanduser("~/.assistant-broker-token")
            if os.path.exists(token_path):
                with open(token_path) as f:
                    self.token = f.read().strip()
            else:
                raise ValueError(
                    "No token found. Set ASSISTANT_BROKER_TOKEN env var "
                    "or create ~/.assistant-broker-token"
                )
        
        self.headers = {
            "Content-Type": "application/json",
            "X-Assistant-Token": self.token
        }
    
    def _request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to broker"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.post(url, json=data, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def health(self) -> Dict[str, str]:
        """Check broker health (no auth required)"""
        resp = requests.get(f"{self.base_url}/v1/health")
        resp.raise_for_status()
        return resp.json()
    
    def open_app(self, bundle_id: str) -> Dict[str, str]:
        """Open macOS application by bundle ID"""
        return self._request("v1/open_app", {"bundle_id": bundle_id})
    
    def quit_app(self, bundle_id: str, force: bool = False) -> Dict[str, str]:
        """Quit macOS application by bundle ID"""
        return self._request("v1/quit_app", {
            "bundle_id": bundle_id,
            "force": force
        })
    
    def run_command(self, cmd: str, args: List[str]) -> Dict[str, str]:
        """Run whitelisted command"""
        return self._request("v1/run", {"cmd": cmd, "args": args})
    
    def write_file(self, path: str, content: str) -> Dict[str, str]:
        """Write file to allowed directory"""
        return self._request("v1/write_file", {"path": path, "content": content})
    
    def read_file(self, path: str) -> str:
        """Read file from allowed directory"""
        result = self._request("v1/read_file", {"path": path})
        return result.get("content", "")
    
    def reveal_in_finder(self, path: str) -> Dict[str, str]:
        """Reveal file/folder in Finder"""
        return self.run_command("open", ["-R", path])
    
    def open_path(self, path: str) -> Dict[str, str]:
        """Open file or application at path"""
        return self.run_command("open", [path])


# Convenience functions
def get_client() -> BrokerClient:
    """Get configured broker client"""
    return BrokerClient()


def open_app(bundle_id: str) -> None:
    """Quick helper to open an app"""
    get_client().open_app(bundle_id)


def reveal(path: str) -> None:
    """Quick helper to reveal path in Finder"""
    get_client().reveal_in_finder(path)


if __name__ == "__main__":
    # Demo usage
    client = BrokerClient()
    
    print("✅ Health check:", client.health())
    print("\n📝 Opening Calculator...")
    client.open_app("com.apple.calculator")
    
    import time
    time.sleep(2)
    
    print("❌ Closing Calculator...")
    client.quit_app("com.apple.calculator")
    
    print("\n✅ Demo complete!")

