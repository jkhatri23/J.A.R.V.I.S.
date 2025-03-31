import webbrowser
import spotipy.exceptions
from .config import get_spotify_client, get_active_device, get_authorization_url
import logging

logger = logging.getLogger(__name__)

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