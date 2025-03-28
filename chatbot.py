from dotenv import load_dotenv
import os
import platform
import requests
from openai import OpenAI
from docx import Document  # Import python-docx for Word document creation
import re
import logging
from typing import Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize client without any additional parameters
client = OpenAI(api_key=api_key)

# API configuration
API_URL = "http://127.0.0.1:8000"

def chat_gpt(prompt):
    """Calls OpenAI API for chatbot response"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def get_default_save_path():
    """Returns the root directory for the operating system."""
    # When running in Docker, use the /host mount point
    if os.path.exists("/host"):
        # Return the /host directory since we're mounting specific directories
        return "/host"
    
    # For local development
    if platform.system() == "Windows":
        return "C:\\"  # Windows root
    elif platform.system() == "Darwin":  # macOS
        return "/"
    else:  # Linux
        return "/"

def find_directory_dfs(start_path: str, target_dir: str) -> Optional[str]:
    """
    Perform a depth-first search to find a directory in the file system.
    Returns the full path if found, None otherwise.
    """
    try:
        # Add logging to debug the search
        logger.debug(f"Starting directory search from: {start_path}")
        logger.debug(f"Looking for directory: {target_dir}")
        
        # Common directories to check first
        common_dirs = [
            os.path.join(start_path, "Desktop"),
            os.path.join(start_path, "Documents"),
            os.path.join(start_path, "Downloads"),
            os.path.join(start_path, "Pictures"),
            os.path.join(start_path, "Music"),
            os.path.join(start_path, "Videos")
        ]
        
        # Check common directories first
        for dir_path in common_dirs:
            if os.path.exists(dir_path) and target_dir.lower() == os.path.basename(dir_path).lower():
                logger.debug(f"Found directory in common paths: {dir_path}")
                return dir_path
        
        # If not found in common directories, check if the target directory exists directly
        target_path = os.path.join(start_path, target_dir)
        if os.path.exists(target_path):
            logger.debug(f"Found directory directly at: {target_path}")
            return target_path
            
        # If still not found, perform a depth-first search
        for root, dirs, _ in os.walk(start_path):
            for dir_name in dirs:
                if dir_name.lower() == target_dir.lower():
                    found_path = os.path.join(root, dir_name)
                    logger.debug(f"Found directory in DFS: {found_path}")
                    return found_path
            
        logger.debug(f"Directory '{target_dir}' not found in the file system")
        return None
    except PermissionError:
        logger.warning(f"Permission denied accessing {start_path}")
    except Exception as e:
        logger.error(f"Error searching directory: {str(e)}")
    return None

def find_file_dfs(start_path: str, target_file: str) -> Optional[str]:
    """
    Perform a depth-first search to find a file in the file system.
    Returns the full path if found, None otherwise.
    """
    try:
        for root, dirs, files in os.walk(start_path):
            if target_file in files:
                return os.path.join(root, target_file)
    except PermissionError:
        logger.warning(f"Permission denied accessing {start_path}")
    except Exception as e:
        logger.error(f"Error searching file: {str(e)}")
    return None

def create_file(file_name: str, content: str, target_dir: Optional[str] = None) -> str:
    """Create a new file with the given content in the specified directory."""
    try:
        # Get the base path from the host filesystem
        base_path = get_default_save_path()
        logger.debug(f"Base path: {base_path}")
        
        if target_dir:
            # Find the target directory using DFS
            found_dir = find_directory_dfs(base_path, target_dir)
            if not found_dir:
                logger.error(f"Directory '{target_dir}' not found in the file system.")
                return f"Directory '{target_dir}' not found in the file system."
            file_path = os.path.join(found_dir, file_name)
            logger.debug(f"Target directory found: {found_dir}")
        else:
            # If no target directory specified, create in Downloads by default
            file_path = os.path.join(base_path, "Downloads", file_name)
            logger.debug("No target directory specified, using Downloads as default")
            
        # Add logging to debug file creation
        logger.debug(f"Creating file at path: {file_path}")
        
        # Ensure the directory exists and has proper permissions
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(content)
            
        # Set proper permissions on the file
        os.chmod(file_path, 0o644)  # Readable by everyone, writable by owner
        
        return f"File '{file_name}' created successfully in {os.path.dirname(file_path)}."
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}")
        return f"Error creating file: {str(e)}"

def delete_file(file_name: str, target_dir: Optional[str] = None) -> str:
    """Delete a file from the specified directory."""
    try:
        # Get the base path from the host filesystem
        base_path = get_default_save_path()
        logger.debug(f"Base path: {base_path}")
        logger.debug(f"Looking for file to delete: {file_name}")
        
        # If target directory is specified, search only in that directory
        if target_dir:
            found_dir = find_directory_dfs(base_path, target_dir)
            if not found_dir:
                logger.error(f"Directory '{target_dir}' not found in the file system.")
                return f"Directory '{target_dir}' not found in the file system."
            file_path = os.path.join(found_dir, file_name)
            logger.debug(f"Looking for file in specified directory: {found_dir}")
        else:
            # Search for the file in the entire filesystem
            # Common directories to check first
            common_dirs = [
                os.path.join(base_path, "Desktop"),
                os.path.join(base_path, "Documents"),
                os.path.join(base_path, "Downloads"),
                os.path.join(base_path, "Pictures"),
                os.path.join(base_path, "Music"),
                os.path.join(base_path, "Videos")
            ]
            
            # Check common directories first
            for dir_path in common_dirs:
                if os.path.exists(dir_path):
                    file_path = os.path.join(dir_path, file_name)
                    if os.path.exists(file_path):
                        logger.debug(f"Found file in common path: {file_path}")
                        break
            else:
                # If not found in common directories, check if the file exists directly
                file_path = os.path.join(base_path, file_name)
                if not os.path.exists(file_path):
                    # If still not found, perform a depth-first search
                    for root, _, files in os.walk(base_path):
                        if file_name in files:
                            file_path = os.path.join(root, file_name)
                            logger.debug(f"Found file in DFS: {file_path}")
                            break
                    else:
                        return f"File '{file_name}' not found in the file system."
            
        logger.debug(f"Attempting to delete file at path: {file_path}")
            
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"File '{file_name}' deleted successfully from {os.path.dirname(file_path)}."
        else:
            return f"File '{file_name}' not found in the file system."
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return f"Error deleting file: {str(e)}"

def find_file(file_name: str) -> str:
    """Find a file in the file system using depth-first search."""
    try:
        # Get the base path from the host filesystem
        base_path = get_default_save_path()
        logger.debug(f"Base path: {base_path}")
        logger.debug(f"Looking for file: {file_name}")
        
        # Common directories to check first
        common_dirs = [
            os.path.join(base_path, "Desktop"),
            os.path.join(base_path, "Documents"),
            os.path.join(base_path, "Downloads"),
            os.path.join(base_path, "Pictures"),
            os.path.join(base_path, "Music"),
            os.path.join(base_path, "Videos")
        ]
        
        # Check common directories first
        for dir_path in common_dirs:
            if os.path.exists(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if os.path.exists(file_path):
                    logger.debug(f"Found file in common path: {file_path}")
                    return f"File '{file_name}' found at: {file_path}"
        
        # If not found in common directories, check if the file exists directly
        direct_path = os.path.join(base_path, file_name)
        if os.path.exists(direct_path):
            logger.debug(f"Found file directly at: {direct_path}")
            return f"File '{file_name}' found at: {direct_path}"
            
        # If still not found, perform a depth-first search
        for root, _, files in os.walk(base_path):
            if file_name in files:
                found_path = os.path.join(root, file_name)
                logger.debug(f"Found file in DFS: {found_path}")
                return f"File '{file_name}' found at: {found_path}"
            
        logger.debug(f"File '{file_name}' not found in the file system")
        return f"File '{file_name}' not found in the file system."
    except PermissionError:
        logger.warning(f"Permission denied accessing {base_path}")
        return f"Permission denied while searching for file '{file_name}'"
    except Exception as e:
        logger.error(f"Error finding file: {str(e)}")
        return f"Error finding file: {str(e)}"

def get_search_paths():
    """Returns a list of directories to search based on the OS"""
    if platform.system() == "Windows":
        return [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            "C:\\Users",  # Searches all user profiles (Windows)
        ]
    else:
        return [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            "/Users",  # MacOS User profiles
            "/home",  # Linux home directories
        ]

def extract_song_name(text):
    """Extract song name from natural language text"""
    text = text.lower().strip()
    
    # Album patterns (most specific first)
    album_patterns = [
        # Album with artist patterns
        r"play\s+(?:the\s+)?album\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)",
        r"queue\s+(?:the\s+)?album\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)",
        r"add\s+(?:the\s+)?album\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)\s+to\s+queue",
        r"play\s+(?:the\s+)?album\s+([^.!?]+?)\s+by\s+([^.!?]+)",
        r"queue\s+(?:the\s+)?album\s+([^.!?]+?)\s+by\s+([^.!?]+)",
        r"add\s+(?:the\s+)?album\s+([^.!?]+?)\s+by\s+([^.!?]+)\s+to\s+queue",
        
        # Album without artist patterns
        r"play\s+(?:the\s+)?album\s+['\"]([^'\"]+)['\"]",
        r"queue\s+(?:the\s+)?album\s+['\"]([^'\"]+)['\"]",
        r"add\s+(?:the\s+)?album\s+['\"]([^'\"]+)['\"]\s+to\s+queue",
        r"play\s+(?:the\s+)?album\s+([^.!?]+)",
        r"queue\s+(?:the\s+)?album\s+([^.!?]+)",
        r"add\s+(?:the\s+)?album\s+([^.!?]+)\s+to\s+queue"
    ]
    
    # Try album patterns first
    for pattern in album_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:
                album, artist = match.groups()
                return f"{album.strip()} {artist.strip()}"
            return match.group(1).strip()
    
    # Podcast patterns (most specific first)
    podcast_patterns = [
        # Podcast with quotes
        r"play\s+(?:the\s+)?podcast\s+['\"]([^'\"]+)['\"]",
        r"queue\s+(?:the\s+)?podcast\s+['\"]([^'\"]+)['\"]",
        r"add\s+(?:the\s+)?podcast\s+['\"]([^'\"]+)['\"]\s+to\s+queue",
        
        # Basic podcast patterns
        r"play\s+(?:the\s+)?podcast\s+([^.!?]+)",
        r"queue\s+(?:the\s+)?podcast\s+([^.!?]+)",
        r"add\s+(?:the\s+)?podcast\s+([^.!?]+)\s+to\s+queue",
        
        # Podcast name patterns
        r"play\s+([^.!?]+?)(?:\s+podcast)?",
        r"queue\s+([^.!?]+?)(?:\s+podcast)?",
        r"add\s+([^.!?]+?)(?:\s+podcast)?\s+to\s+queue"
    ]
    
    # Try podcast patterns
    for pattern in podcast_patterns:
        match = re.search(pattern, text)
        if match:
            podcast_name = match.group(1).strip()
            return podcast_name
    
    # Common patterns for music requests (most specific first)
    patterns = [
        # Play with artist patterns (most specific first)
        r"play\s+(?:the\s+)?song\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)",
        r"play\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)",
        r"play\s+([^.!?]+?)\s+by\s+([^.!?]+)",
        r"play\s+([^.!?]+?)\s+from\s+([^.!?]+)",
        
        # Queue with artist patterns
        r"queue\s+(?:the\s+)?song\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)",
        r"queue\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)",
        r"queue\s+([^.!?]+?)\s+by\s+([^.!?]+)",
        r"queue\s+([^.!?]+?)\s+from\s+([^.!?]+)",
        
        # Add to queue with artist patterns
        r"add\s+(?:the\s+)?song\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)\s+to\s+queue",
        r"add\s+['\"]([^'\"]+)['\"]\s+by\s+([^.!?]+)\s+to\s+queue",
        r"add\s+([^.!?]+?)\s+by\s+([^.!?]+)\s+to\s+queue",
        r"add\s+([^.!?]+?)\s+from\s+([^.!?]+)\s+to\s+queue",
        
        # Basic play patterns with quotes
        r"play\s+(?:the\s+)?song\s+(?:called\s+)?['\"]([^'\"]+)['\"]",
        r"play\s+['\"]([^'\"]+)['\"]",
        
        # Basic queue patterns with quotes
        r"queue\s+(?:the\s+)?song\s+(?:called\s+)?['\"]([^'\"]+)['\"]",
        r"queue\s+['\"]([^'\"]+)['\"]",
        
        # Basic add to queue patterns with quotes
        r"add\s+(?:the\s+)?song\s+(?:called\s+)?['\"]([^'\"]+)['\"]\s+to\s+queue",
        r"add\s+['\"]([^'\"]+)['\"]\s+to\s+queue"
    ]
    
    # First try to match with artist
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # If we have both song and artist, combine them for better search
            if len(match.groups()) == 2:
                song, artist = match.groups()
                return f"{song.strip()} {artist.strip()}"
            return match.group(1).strip()
    
    # If no match found, try to extract just the song name after "play" or "queue"
    basic_patterns = [
        r"play\s+(?:the\s+)?song\s+([^.!?]+)",
        r"queue\s+(?:the\s+)?song\s+([^.!?]+)",
        r"add\s+(?:the\s+)?song\s+([^.!?]+)\s+to\s+queue",
        r"play\s+([^.!?]+)",
        r"queue\s+([^.!?]+)",
        r"add\s+([^.!?]+)\s+to\s+queue"
    ]
    
    for pattern in basic_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return None

def send_spotify_request(endpoint, song_name):
    """Helper function to send Spotify API requests."""
    try:
        url = f"{API_URL}/spotify/{endpoint}"
        print(f"Debug: Sending request to {url} with song: {song_name}")  # Debug line
        response = requests.post(url, json={"song_name": song_name})
        print(f"Debug: Response status code: {response.status_code}")  # Debug line
        print(f"Debug: Response content: {response.text}")  # Debug line
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Debug: Request failed with error: {str(e)}")  # Debug line
        return {"error": f"Failed to connect to Spotify service: {str(e)}"}

def handle_music_request(text):
    """Handle natural language music requests"""
    song_name = extract_song_name(text)
    if not song_name:
        return "I couldn't understand which song, album, or podcast you want to play. Could you please specify the name?"

    # Determine if it's a play or queue request
    is_queue_request = any(word in text.lower() for word in ["queue", "add to queue"])
    
    # Determine if it's a podcast request
    is_podcast_request = any(word in text.lower() for word in ["podcast"])
    
    # Determine if it's an album request
    is_album_request = any(word in text.lower() for word in ["album"])
    
    # Determine the appropriate endpoint
    if is_podcast_request:
        endpoint = "queue-podcast" if is_queue_request else "play-podcast"
        action = "queued" if is_queue_request else "playing"
    elif is_album_request:
        endpoint = "queue-album" if is_queue_request else "play-album"
        action = "queued" if is_queue_request else "playing"
    else:
        endpoint = "queue-song" if is_queue_request else "play-song"
        action = "queued" if is_queue_request else "playing"

    result = send_spotify_request(endpoint, song_name)

    if "error" in result:
        if "User not logged in" in result["error"]:
            return f"Please authenticate with Spotify first by visiting: {API_URL}/spotify/authorize"
        return f"Error: {result['error']}"
    
    if "success" in result:
        return result["success"]
    
    return f"Successfully {action}: {song_name}"

def chatbot():
    print("Chatbot is ready! You can ask me to:")
    print("- Play songs (e.g., 'play Shape of You' or 'play the song called Shape of You')")
    print("- Queue songs (e.g., 'queue Blinding Lights' or 'add Shape of You to queue')")
    print("- Play albums (e.g., 'play album Scorpion by Drake' or 'play the album Scorpion')")
    print("- Queue albums (e.g., 'queue album Scorpion by Drake' or 'add album Scorpion to queue')")
    print("- Play podcasts (e.g., 'play podcast Impaulsive' or 'play The Joe Rogan Experience')")
    print("- Queue podcasts (e.g., 'queue podcast Impaulsive' or 'add The Joe Rogan Experience to queue')")
    print("- Create files in specific directories (e.g., 'create file test.txt in Documents')")
    print("- Delete files from specific directories (e.g., 'delete file test.txt from Documents')")
    print("- Find files in the system (e.g., 'find file test.txt')")
    print("- Or just chat with me!")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        # Check if user wants to delete a file
        elif user_input.lower().startswith("delete file "):
            parts = user_input[12:].strip().split(" from ")
            if len(parts) == 2:
                filename, target_dir = parts
                result = delete_file(filename.strip(), target_dir.strip())
            else:
                filename = parts[0]
                result = delete_file(filename.strip())
            print(f"Chatbot: {result}")

        # Check if user wants to create a file
        elif user_input.lower().startswith("create file "):
            parts = user_input[12:].strip().split(" in ")
            if len(parts) == 2:
                filename, target_dir = parts
                content = input("Enter file content (or leave blank for an empty file): ")
                result = create_file(filename.strip(), content, target_dir.strip())
            else:
                filename = parts[0]
                content = input("Enter file content (or leave blank for an empty file): ")
                result = create_file(filename.strip(), content)
            print(f"Chatbot: {result}")

        # Check if user wants to find a file
        elif user_input.lower().startswith("find file "):
            filename = user_input[10:].strip()
            result = find_file(filename)
            print(f"Chatbot: {result}")

        # First check if it's a music request
        elif any(word in user_input.lower() for word in ["play", "queue", "song", "music", "spotify"]):
            print(f"Debug: Detected music request: {user_input}")  # Debug line
            song_name = extract_song_name(user_input)
            if song_name:
                print(f"Debug: Extracted song name: {song_name}")  # Debug line
                response = handle_music_request(user_input)
                print(f"Chatbot: {response}")
                continue
            else:
                print(f"Debug: No song name extracted from: {user_input}")  # Debug line

        else:
            try:
                # Get a response from ChatGPT
                chatbot_reply = chat_gpt(user_input)
                print(f"Chatbot: {chatbot_reply}")
            except Exception as e:
                print(f"Error: {e}")

# Start the chatbot
if __name__ == "__main__":
    chatbot()
