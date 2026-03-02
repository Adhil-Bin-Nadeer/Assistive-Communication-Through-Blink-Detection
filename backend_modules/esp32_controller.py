import requests
from backend_modules.config import ESP32_CONFIG
import time
from typing import Dict, Optional, Tuple

class ESP32Controller:
    """
    Controller module for communicating with ESP32 for room device control.
    Supports HTTP/REST API communication with ESP32 web server.
    """
    
    def __init__(self, esp32_ip: str = None, port: int = None, timeout: int = None):
        """
        Initialize ESP32 controller.
        
        Args:
            esp32_ip: IP address of the ESP32 device (default from config)
            port: HTTP port (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.esp32_ip = esp32_ip if esp32_ip is not None else ESP32_CONFIG["ip"]
        self.port = port if port is not None else ESP32_CONFIG["port"]
        self.timeout = timeout if timeout is not None else ESP32_CONFIG["timeout"]
        self.base_url = f"http://{self.esp32_ip}:{self.port}"
        self.device_states = {}  # Track device states locally
        
        print(f"[ESP32Controller] Initialized with IP: {self.esp32_ip}:{self.port}")
    
    def update_ip(self, new_ip: str, port: Optional[int] = None):
        """Update ESP32 IP address and port."""
        self.esp32_ip = new_ip
        if port:
            self.port = port
        self.base_url = f"http://{self.esp32_ip}:{self.port}"
        print(f"[ESP32Controller] Updated IP to: {self.esp32_ip}:{self.port}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to ESP32.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.get(f"{self.base_url}/ping", timeout=self.timeout)
            if response.status_code == 200:
                return True, "ESP32 connection successful"
            else:
                return False, f"ESP32 responded with status code: {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "Connection timeout - ESP32 not responding"
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to ESP32 at {self.esp32_ip}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def control_device(self, device: str, action: str) -> Dict[str, any]:
        """
        Send control command to ESP32 for a specific device.
        
        Args:
            device: Device name (e.g., 'light1', 'light2', 'fan', 'ac')
            action: Action to perform ('on', 'off', 'toggle')
            
        Returns:
            Dict with status, message, and device state
        """
        try:
            # Normalize inputs
            device = device.lower().strip()
            action = action.lower().strip()
            
            # Validate action
            if action not in ['on', 'off', 'toggle']:
                return {
                    "status": "error",
                    "message": f"Invalid action '{action}'. Use 'on', 'off', or 'toggle'",
                    "device": device,
                    "state": None
                }
            
            # Build request URL (adjust based on your ESP32 API structure)
            # Common patterns:
            # Pattern 1: /device/light1/on
            # Pattern 2: /control?device=light1&action=on
            # Using Pattern 1 as default
            url = f"{self.base_url}/device/{device}/{action}"
            
            print(f"[ESP32Controller] Sending request to: {url}")
            
            # Send HTTP GET request to ESP32
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                # Parse response (assuming JSON response)
                try:
                    data = response.json()
                    new_state = data.get('state', action)
                except:
                    # If not JSON, assume success
                    new_state = action if action in ['on', 'off'] else 'unknown'
                
                # Update local state tracking
                self.device_states[device] = new_state
                
                return {
                    "status": "success",
                    "message": f"Device '{device}' turned {action.upper()}",
                    "device": device,
                    "state": new_state
                }
            else:
                return {
                    "status": "error",
                    "message": f"ESP32 returned status code: {response.status_code}",
                    "device": device,
                    "state": None
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": f"Request timeout - ESP32 not responding",
                "device": device,
                "state": None
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"Cannot connect to ESP32 at {self.esp32_ip}",
                "device": device,
                "state": None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error controlling device: {str(e)}",
                "device": device,
                "state": None
            }
    
    def control_device_post(self, device: str, action: str, data: Optional[Dict] = None) -> Dict[str, any]:
        """
        Send control command to ESP32 using POST request (for more complex commands).
        
        Args:
            device: Device name
            action: Action to perform
            data: Additional data to send in POST body (e.g., brightness level, temperature)
            
        Returns:
            Dict with status, message, and device state
        """
        try:
            url = f"{self.base_url}/device/{device}/{action}"
            
            payload = data or {}
            payload['device'] = device
            payload['action'] = action
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    new_state = result.get('state', action)
                except:
                    new_state = action
                
                self.device_states[device] = new_state
                
                return {
                    "status": "success",
                    "message": f"Device '{device}' controlled successfully",
                    "device": device,
                    "state": new_state
                }
            else:
                return {
                    "status": "error",
                    "message": f"ESP32 returned status code: {response.status_code}",
                    "device": device,
                    "state": None
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "device": device,
                "state": None
            }
    
    def get_device_state(self, device: str) -> Dict[str, any]:
        """
        Query current state of a device from ESP32.
        
        Args:
            device: Device name
            
        Returns:
            Dict with status, device name, and current state
        """
        try:
            url = f"{self.base_url}/device/{device}/status"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    state = data.get('state', 'unknown')
                except:
                    state = 'unknown'
                
                self.device_states[device] = state
                
                return {
                    "status": "success",
                    "device": device,
                    "state": state
                }
            else:
                # Return locally cached state if available
                cached_state = self.device_states.get(device, 'unknown')
                return {
                    "status": "partial",
                    "device": device,
                    "state": cached_state,
                    "message": "Using cached state"
                }
                
        except Exception as e:
            # Return locally cached state
            cached_state = self.device_states.get(device, 'unknown')
            return {
                "status": "error",
                "device": device,
                "state": cached_state,
                "message": f"Error: {str(e)}"
            }
    
    def get_all_devices(self) -> Dict[str, any]:
        """
        Get status of all devices from ESP32.
        
        Returns:
            Dict with status and device states
        """
        try:
            url = f"{self.base_url}/devices/all"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    devices = data.get('devices', {})
                    self.device_states.update(devices)
                    return {
                        "status": "success",
                        "devices": devices
                    }
                except:
                    return {
                        "status": "error",
                        "message": "Invalid response format"
                    }
            else:
                # Return cached states
                return {
                    "status": "partial",
                    "devices": self.device_states,
                    "message": "Using cached states"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "devices": self.device_states,
                "message": f"Error: {str(e)}"
            }
    
    def turn_all_off(self) -> Dict[str, any]:
        """
        Turn off all devices.
        
        Returns:
            Dict with status and results for each device
        """
        try:
            url = f"{self.base_url}/devices/alloff"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                # Update all local states to 'off'
                for device in self.device_states:
                    self.device_states[device] = 'off'
                
                return {
                    "status": "success",
                    "message": "All devices turned off"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed with status code: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize controller with your ESP32 IP
    controller = ESP32Controller(esp32_ip="192.168.1.100")
    
    # Test connection
    connected, msg = controller.test_connection()
    print(f"Connection test: {msg}")
    
    if connected:
        # Control a light
        result = controller.control_device("light1", "on")
        print(f"Control result: {result}")
        
        # Get device state
        state = controller.get_device_state("light1")
        print(f"Device state: {state}")
        
        # Get all devices
        all_devices = controller.get_all_devices()
        print(f"All devices: {all_devices}")
