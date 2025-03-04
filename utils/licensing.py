import hashlib
import json
import os
import platform
import uuid
import requests
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings, QTimer, QObject, pyqtSignal

class LicenseManager(QObject):
    """
    License manager for the application
    Handles license validation, activation, and expiration
    """
    
    # Signals
    license_valid = pyqtSignal()
    license_invalid = pyqtSignal(str)
    license_expired = pyqtSignal(int)  # Days remaining
    license_expiring_soon = pyqtSignal(int)  # Days remaining
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("EmployeeApp", "License")
        self.license_key = self.settings.value("license_key", "")
        self.activation_date = self.settings.value("activation_date", "")
        self.expiration_date = self.settings.value("expiration_date", "")
        self.hardware_id = self._generate_hardware_id()
        self.activation_server = "https://license.example.com/api/validate"
        
        # Set up timer to check license validity daily
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.validate_license)
        self.check_timer.start(24 * 60 * 60 * 1000)  # Check once per day
        
    def _generate_hardware_id(self):
        """Generate a unique hardware ID based on system information"""
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "node": platform.node()
        }
        
        # Get MAC address (fallback to a random UUID if not available)
        try:
            mac = uuid.getnode()
            if mac != uuid.getnode():  # Check if a real MAC was returned
                mac = uuid.uuid4().hex
        except:
            mac = uuid.uuid4().hex
            
        system_info["mac"] = str(mac)
        
        # Create a hash of the system info
        system_str = json.dumps(system_info, sort_keys=True)
        return hashlib.sha256(system_str.encode()).hexdigest()
    
    def activate_license(self, license_key):
        """Activate the license with the provided key"""
        try:
            # In a real implementation, this would make an API call to the license server
            # For demo purposes, we'll simulate a successful activation
            
            # In production, uncomment this code to make an actual API call
            # response = requests.post(
            #     self.activation_server,
            #     json={
            #         "license_key": license_key,
            #         "hardware_id": self.hardware_id
            #     }
            # )
            # if response.status_code != 200:
            #     return False, "Failed to activate license. Server response: " + response.text
            # 
            # data = response.json()
            # if not data.get("success"):
            #     return False, data.get("message", "Unknown error")
            
            # For demo, simulate a successful activation
            # In production, these values would come from the server response
            self.license_key = license_key
            self.activation_date = datetime.now().isoformat()
            self.expiration_date = (datetime.now() + timedelta(days=365)).isoformat()
            
            # Save license information
            self.settings.setValue("license_key", self.license_key)
            self.settings.setValue("activation_date", self.activation_date)
            self.settings.setValue("expiration_date", self.expiration_date)
            self.settings.setValue("hardware_id", self.hardware_id)
            
            return True, "License activated successfully"
        except Exception as e:
            return False, f"Error activating license: {str(e)}"
    
    def validate_license(self):
        """Validate the current license"""
        if not self.license_key or not self.expiration_date:
            self.license_invalid.emit("No valid license found")
            return False
        
        try:
            # Check if license has expired
            expiration = datetime.fromisoformat(self.expiration_date)
            now = datetime.now()
            
            if now > expiration:
                self.license_invalid.emit("License has expired")
                return False
            
            # Check days remaining
            days_remaining = (expiration - now).days
            
            # Emit warning if license is expiring soon (within 30 days)
            if days_remaining <= 30:
                self.license_expiring_soon.emit(days_remaining)
            
            # In a real implementation, you would also verify with the license server
            # that the license is still valid (not revoked, etc.)
            
            self.license_valid.emit()
            return True
        except Exception as e:
            self.license_invalid.emit(f"Error validating license: {str(e)}")
            return False
    
    def get_license_info(self):
        """Get information about the current license"""
        if not self.license_key:
            return {
                "status": "Not Activated",
                "license_key": "",
                "activation_date": "",
                "expiration_date": "",
                "days_remaining": 0
            }
        
        try:
            expiration = datetime.fromisoformat(self.expiration_date)
            activation = datetime.fromisoformat(self.activation_date)
            now = datetime.now()
            days_remaining = max(0, (expiration - now).days)
            
            status = "Active"
            if now > expiration:
                status = "Expired"
            elif days_remaining <= 30:
                status = f"Expiring Soon ({days_remaining} days)"
                
            return {
                "status": status,
                "license_key": self.license_key,
                "activation_date": activation.strftime("%Y-%m-%d"),
                "expiration_date": expiration.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining
            }
        except Exception:
            return {
                "status": "Error",
                "license_key": self.license_key,
                "activation_date": self.activation_date,
                "expiration_date": self.expiration_date,
                "days_remaining": 0
            }
