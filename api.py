from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import chat_gpt, create_file, delete_file
from fastapi.responses import RedirectResponse, HTMLResponse
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Import spotify module after app initialization
try:
    from spotify import (
        play_song, queue_song, play_album, queue_album,
        play_podcast, queue_podcast, get_authorization_url, sp_oauth
    )
    logger.info("Successfully imported spotify module")
except Exception as e:
    logger.error(f"Failed to import spotify module: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

class ChatRequest(BaseModel):
    prompt: str

class FileRequest(BaseModel):
    filename: str
    content: str = ""  # Default content is empty if not provided

class SpotifyRequest(BaseModel):
    song_name: str

@app.post("/chat")
async def chat(request: ChatRequest):
    response = chat_gpt(request.prompt)
    return {"response": response}

@app.post("/delete-file")
async def delete_file_api(request: FileRequest):
    response = delete_file(request.filename)
    return {"response": response}

@app.post("/create-file")
async def create_file_api(request: FileRequest):
    response = create_file(request.filename, request.content)
    return {"response": response}

@app.post("/spotify/play-song")
async def spotify_play_song(request: SpotifyRequest):
    """Endpoint to play a song via Spotify."""
    try:
        response = play_song(request.song_name)
        return response
    except Exception as e:
        logger.error(f"Error playing song: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/spotify/queue-song")
async def spotify_queue_song(request: SpotifyRequest):
    """Endpoint to queue a song in Spotify."""
    try:
        response = queue_song(request.song_name)
        return response
    except Exception as e:
        logger.error(f"Error queueing song: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/spotify/play-album")
async def spotify_play_album(request: SpotifyRequest):
    """Endpoint to play an album via Spotify."""
    try:
        response = play_album(request.song_name)
        return response
    except Exception as e:
        logger.error(f"Error playing album: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/spotify/queue-album")
async def spotify_queue_album(request: SpotifyRequest):
    """Endpoint to queue an album in Spotify."""
    try:
        response = queue_album(request.song_name)
        return response
    except Exception as e:
        logger.error(f"Error queueing album: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/spotify/play-podcast")
async def spotify_play_podcast(request: SpotifyRequest):
    """Endpoint to play a podcast via Spotify."""
    try:
        response = play_podcast(request.song_name)
        return response
    except Exception as e:
        logger.error(f"Error playing podcast: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/spotify/queue-podcast")
async def spotify_queue_podcast(request: SpotifyRequest):
    """Endpoint to queue a podcast in Spotify."""
    try:
        response = queue_podcast(request.song_name)
        return response
    except Exception as e:
        logger.error(f"Error queueing podcast: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spotify/authorize")
async def spotify_authorize():
    """Route to redirect the user for Spotify authorization."""
    try:
        logger.info("Starting Spotify authorization process")
        auth_url = get_authorization_url()
        logger.info(f"Generated authorization URL: {auth_url}")
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error during Spotify authorization: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spotify/callback")
async def spotify_callback(code: str):
    """Spotify OAuth callback route to get the access token."""
    try:
        logger.info("Received Spotify callback with code")
        token_info = sp_oauth.get_access_token(code)
        if not token_info:
            logger.error("Failed to get access token")
            raise HTTPException(status_code=400, detail="Failed to authenticate with Spotify.")
        
        # The token is automatically cached by spotipy when using get_access_token
        logger.info("Successfully authenticated with Spotify")
        
        # Return an HTML page that closes the popup and refreshes the parent window
        return HTMLResponse("""
            <html>
                <body>
                    <script>
                        window.opener.postMessage('spotify-auth-success', '*');
                        window.close();
                    </script>
                </body>
            </html>
        """)
    except Exception as e:
        logger.error(f"Error during Spotify callback: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
