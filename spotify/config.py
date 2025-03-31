from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# Log configuration (without exposing secrets)
logger.info(f"Spotify configuration loaded - Redirect URI: {SPOTIPY_REDIRECT_URI}")

# Initialize Spotify OAuth
try:
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
        open_browser=False,
        cache_path=".spotify_caches"  # Specify cache file location
    )
    logger.info("Successfully initialized Spotify OAuth")
except Exception as e:
    logger.error(f"Failed to initialize Spotify OAuth: {str(e)}")
    raise

def get_spotify_client():
    """Retrieve authenticated Spotify client."""
    try:
        token_info = sp_oauth.get_cached_token()
        if not token_info or 'access_token' not in token_info:
            logger.info("No valid token found, user needs to authenticate")
            return None
        logger.info("Successfully retrieved Spotify client")
        return spotipy.Spotify(auth=token_info["access_token"])
    except Exception as e:
        logger.error(f"Error getting Spotify client: {str(e)}")
        return None

def get_authorization_url():
    """Get the URL for the user to authenticate and authorize the app."""
    try:
        auth_url = sp_oauth.get_authorize_url()
        logger.info(f"Generated authorization URL: {auth_url}")
        return auth_url
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")

def get_active_device(sp):
    """Get the currently active Spotify device."""
    try:
        # Get current playback state
        current_playback = sp.current_playback()
        logger.info(f"Current playback state: {current_playback}")
        
        # If there's an active device, return its ID
        if current_playback and current_playback.get('device'):
            device = current_playback['device']
            logger.info(f"Found currently playing device: {device.get('name')} ({device.get('type')})")
            return device['id']
        
        # If no active device, get list of devices
        devices = sp.devices()
        logger.info(f"All available devices: {devices}")
        
        if not devices['devices']:
            logger.warning("No Spotify devices found")
            return None
            
        # Log all available devices
        logger.info("Available Spotify devices:")
        for device in devices['devices']:
            logger.info(f"- {device.get('name')} ({device.get('type')}) - Active: {device.get('is_active')} - ID: {device.get('id')}")
            
        # Find the active device
        active_device = next((device for device in devices['devices'] if device.get('is_active')), None)
        if active_device:
            logger.info(f"Found active device: {active_device.get('name')} ({active_device.get('type')})")
            return active_device['id']
            
        # If no active device found, try to find a web player or desktop app
        preferred_devices = []
        for device in devices['devices']:
            device_type = device.get('type', '').lower()
            device_name = device.get('name', '').lower()
            
            # Prioritize web players and desktop apps
            if (device_type in ['computer', 'web', 'browser'] or 
                'chrome' in device_name or 
                'spotify' in device_name or 
                'web player' in device_name or
                'browser' in device_name):
                preferred_devices.append(device)
                logger.info(f"Found preferred device: {device.get('name')} ({device.get('type')})")
        
        # If we found preferred devices, use the first one
        if preferred_devices:
            device = preferred_devices[0]
            logger.info(f"Using preferred device: {device.get('name')} ({device.get('type')})")
            return device['id']
            
        # If no preferred devices found, return the first available device
        device = devices['devices'][0]
        logger.info(f"No preferred devices found, using first available: {device.get('name')} ({device.get('type')})")
        return device['id']
    except Exception as e:
        logger.error(f"Error getting active device: {str(e)}")
        return None 