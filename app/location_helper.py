"""
Location Helper - Automatically fetch location using IP geolocation
"""

import requests
from typing import Optional, Dict


def get_current_location() -> Optional[str]:
    """
    Get current location based on IP address
    
    Returns:
        Location string (e.g., "City, Country") or None if failed
    """
    try:
        # Using ipapi.co for free IP geolocation
        response = requests.get('https://ipapi.co/json/', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Build location string
            parts = []
            if data.get('city'):
                parts.append(data['city'])
            if data.get('region'):
                parts.append(data['region'])
            if data.get('country_name'):
                parts.append(data['country_name'])
            
            if parts:
                return ', '.join(parts)
        
        return None
    except Exception as e:
        print(f"Error fetching location: {e}")
        return None


def get_location_details() -> Optional[Dict]:
    """
    Get detailed location information
    
    Returns:
        Dictionary with location details or None if failed
    """
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country_name', 'Unknown'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'timezone': data.get('timezone', 'Unknown')
            }
        
        return None
    except Exception as e:
        print(f"Error fetching location details: {e}")
        return None
