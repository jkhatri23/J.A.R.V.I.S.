from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import webbrowser
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
import logging
import json

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
        
        # If there's an active device, return its ID
        if current_playback and current_playback.get('device'):
            device = current_playback['device']
            logger.info(f"Found currently playing device: {device.get('name')} ({device.get('type')})")
            return device['id']
        
        # If no active device, get list of devices
        devices = sp.devices()
        if not devices['devices']:
            logger.warning("No Spotify devices found")
            return None
            
        # Log all available devices
        logger.info("Available Spotify devices:")
        for device in devices['devices']:
            logger.info(f"- {device.get('name')} ({device.get('type')}) - Active: {device.get('is_active')}")
            
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

def play_song(song_name: str):
    """Function to play a song via Spotify."""
    try:
        sp = get_spotify_client()
        if not sp:
            logger.info("User not authenticated, returning authorization URL")
            return {"error": "User not logged in. Please authenticate with Spotify.", "authorization_url": get_authorization_url()}

        device_id = get_active_device(sp)
        if not device_id:
            logger.warning("No active Spotify devices found")
            return {"error": "No active Spotify devices found."}

        logger.info(f"Found active device: {device_id}")

        result = sp.search(q=song_name, type="track", limit=1)
        if not result['tracks']['items']:
            logger.warning(f"No results found for song: {song_name}")
            return {"error": "Song not found."}

        song = result['tracks']['items'][0]
        song_uri = song['uri']
        song_url = song['external_urls']['spotify']

        logger.info(f"Starting playback of: {song['name']} by {song['artists'][0]['name']}")
        sp.start_playback(device_id=device_id, uris=[song_uri])
        webbrowser.open(song_url)

        return {"success": f"Playing: {song['name']} by {song['artists'][0]['name']}"}

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in play_song: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def queue_song(song_name: str):
    """Function to queue a song in Spotify."""
    try:
        sp = get_spotify_client()
        if not sp:
            logger.info("User not authenticated, returning authorization URL")
            return {"error": "User not logged in. Please authenticate with Spotify.", "authorization_url": get_authorization_url()}

        device_id = get_active_device(sp)
        if not device_id:
            logger.warning("No active Spotify devices found")
            return {"error": "No active Spotify devices found. Please open Spotify on your device and try again."}

        logger.info(f"Found active device: {device_id}")

        result = sp.search(q=song_name, type="track", limit=1)
        if not result['tracks']['items']:
            logger.warning(f"No results found for song: {song_name}")
            return {"error": "Song not found."}

        song = result['tracks']['items'][0]
        song_uri = song['uri']
        
        try:
            logger.info(f"Adding to queue: {song['name']} by {song['artists'][0]['name']}")
            sp.add_to_queue(uri=song_uri, device_id=device_id)
            return {"success": f"Queued: {song['name']} by {song['artists'][0]['name']}"}
        except spotipy.exceptions.SpotifyException as e:
            if "Not found" in str(e):
                logger.warning("Device not found, trying without device_id")
                sp.add_to_queue(uri=song_uri)
                return {"success": f"Queued: {song['name']} by {song['artists'][0]['name']}"}
            raise
    
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in queue_song: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def play_album(album_name: str):
    """Function to play an album via Spotify."""
    try:
        sp = get_spotify_client()
        if not sp:
            logger.info("User not authenticated, returning authorization URL")
            return {"error": "User not logged in. Please authenticate with Spotify.", "authorization_url": get_authorization_url()}

        device_id = get_active_device(sp)
        if not device_id:
            logger.warning("No active Spotify devices found")
            return {"error": "No active Spotify devices found."}

        logger.info(f"Found active device: {device_id}")

        result = sp.search(q=album_name, type="album", limit=1)
        if not result['albums']['items']:
            logger.warning(f"No results found for album: {album_name}")
            return {"error": "Album not found."}

        album = result['albums']['items'][0]
        album_uri = album['uri']
        album_url = album['external_urls']['spotify']

        album_name = album['name']
        artist_name = album['artists'][0]['name']
        total_tracks = album['total_tracks']

        logger.info(f"Starting playback of album: {album_name} by {artist_name} ({total_tracks} tracks)")
        
        sp.start_playback(device_id=device_id, context_uri=album_uri)
        webbrowser.open(album_url)

        return {"success": f"Playing album: {album_name} by {artist_name} ({total_tracks} tracks)"}

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in play_album: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def queue_album(album_name: str):
    """Function to queue an album in Spotify."""
    try:
        sp = get_spotify_client()
        if not sp:
            logger.info("User not authenticated, returning authorization URL")
            return {"error": "User not logged in. Please authenticate with Spotify.", "authorization_url": get_authorization_url()}

        device_id = get_active_device(sp)
        if not device_id:
            logger.warning("No active Spotify devices found")
            return {"error": "No active Spotify devices found. Please open Spotify on your device and try again."}

        logger.info(f"Found active device: {device_id}")

        result = sp.search(q=album_name, type="album", limit=1)
        if not result['albums']['items']:
            logger.warning(f"No results found for album: {album_name}")
            return {"error": "Album not found."}

        album = result['albums']['items'][0]
        album_uri = album['uri']
        
        album_tracks = sp.album_tracks(album_uri)
        track_uris = [track['uri'] for track in album_tracks['items']]
        
        for track_uri in track_uris:
            try:
                sp.add_to_queue(uri=track_uri, device_id=device_id)
            except spotipy.exceptions.SpotifyException as e:
                if "Not found" in str(e):
                    sp.add_to_queue(uri=track_uri)
                else:
                    raise

        return {"success": f"Queued album: {album['name']} by {album['artists'][0]['name']}"}

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in queue_album: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def play_podcast(podcast_name: str):
    """Function to play a podcast via Spotify."""
    try:
        sp = get_spotify_client()
        if not sp:
            logger.info("User not authenticated, returning authorization URL")
            return {"error": "User not logged in. Please authenticate with Spotify.", "authorization_url": get_authorization_url()}

        device_id = get_active_device(sp)
        if not device_id:
            logger.warning("No active Spotify devices found")
            return {"error": "No active Spotify devices found."}

        logger.info(f"Found active device: {device_id}")

        result = sp.search(q=podcast_name, type="show", limit=1)
        if not result['shows']['items']:
            logger.warning(f"No results found for podcast: {podcast_name}")
            return {"error": "Podcast not found."}

        show = result['shows']['items'][0]
        show_uri = show['uri']
        show_url = show['external_urls']['spotify']

        episodes = sp.show_episodes(show_uri, limit=1)
        if not episodes['items']:
            return {"error": "No episodes found for this podcast."}

        episode_uri = episodes['items'][0]['uri']
        episode_name = episodes['items'][0]['name']

        logger.info(f"Starting playback of podcast: {show['name']} - {episode_name}")
        sp.start_playback(device_id=device_id, uris=[episode_uri])
        webbrowser.open(show_url)

        return {"success": f"Playing podcast: {show['name']} - {episode_name}"}

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in play_podcast: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def queue_podcast(podcast_name: str):
    """Function to queue a podcast episode in Spotify."""
    try:
        sp = get_spotify_client()
        if not sp:
            logger.info("User not authenticated, returning authorization URL")
            return {"error": "User not logged in. Please authenticate with Spotify.", "authorization_url": get_authorization_url()}

        device_id = get_active_device(sp)
        if not device_id:
            logger.warning("No active Spotify devices found")
            return {"error": "No active Spotify devices found. Please open Spotify on your device and try again."}

        logger.info(f"Found active device: {device_id}")

        result = sp.search(q=podcast_name, type="show", limit=1)
        if not result['shows']['items']:
            logger.warning(f"No results found for podcast: {podcast_name}")
            return {"error": "Podcast not found."}

        show = result['shows']['items'][0]
        show_uri = show['uri']

        episodes = sp.show_episodes(show_uri, limit=1)
        if not episodes['items']:
            return {"error": "No episodes found for this podcast."}

        episode = episodes['items'][0]
        episode_uri = episode['uri']
        
        try:
            logger.info(f"Adding to queue: {show['name']} - {episode['name']}")
            sp.add_to_queue(uri=episode_uri, device_id=device_id)
            return {"success": f"Queued podcast: {show['name']} - {episode['name']}"}
        except spotipy.exceptions.SpotifyException as e:
            if "Not found" in str(e):
                logger.warning("Device not found, trying without device_id")
                sp.add_to_queue(uri=episode_uri)
                return {"success": f"Queued podcast: {show['name']} - {episode['name']}"}
            raise

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in queue_podcast: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
