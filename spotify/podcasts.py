import webbrowser
import spotipy.exceptions
from .config import get_spotify_client, get_active_device, get_authorization_url
import logging

logger = logging.getLogger(__name__)

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