import webbrowser
import spotipy.exceptions
from .config import get_spotify_client, get_active_device, get_authorization_url
import logging

logger = logging.getLogger(__name__)

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