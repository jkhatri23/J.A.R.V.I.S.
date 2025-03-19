from dotenv import load_dotenv
import os
import platform
import requests
from openai import OpenAI
from docx import Document  # Import python-docx for Word document creation
import re

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    """Returns the correct Downloads folder for Windows, Mac, and Linux."""
    if platform.system() == "Windows":
        return os.path.join(os.environ["USERPROFILE"], "Downloads")  # Windows
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads")  # Mac/Linux

def create_file(filename, content=""):
    """Creates a new file in the Downloads folder with optional content"""
    save_path = get_default_save_path()
    os.makedirs(save_path, exist_ok=True)  # Ensure Downloads folder exists

    file_path = os.path.join(save_path, filename)

    if os.path.exists(file_path):
        confirm = input(f"⚠️ File '{filename}' already exists. Overwrite? (yes/no): ").strip().lower()
        if confirm != 'yes':
            return f"❌ File '{filename}' was NOT overwritten."

    try:
        # If file is a .docx, create it properly
        if filename.endswith(".docx"):
            doc = Document()
            doc.add_paragraph(content)
            doc.save(file_path)
        else:  # Otherwise, treat it as a normal text file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        return f"✅ File '{filename}' created successfully at: {file_path}"
    except Exception as e:
        return f"⚠️ Error creating file '{filename}': {e}"

def find_file(filename):
    """Search for the file in common directories"""
    search_paths = get_search_paths()

    for search_path in search_paths:
        for root, _, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)  # Return full file path
    return None  # File not found

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

def delete_file(filename):
    """Finds and deletes a file by name"""
    file_path = find_file(filename)

    if file_path:
        try:
            os.remove(file_path)
            return f"✅ File '{filename}' deleted successfully from: {file_path}"
        except Exception as e:
            return f"⚠️ Error deleting '{filename}': {e}"
    else:
        return f"❌ File '{filename}' not found."

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
    print("- Create or delete files")
    print("- Or just chat with me!")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        # First check if it's a music request
        if any(word in user_input.lower() for word in ["play", "queue", "song", "music", "spotify"]):
            print(f"Debug: Detected music request: {user_input}")  # Debug line
            song_name = extract_song_name(user_input)
            if song_name:
                print(f"Debug: Extracted song name: {song_name}")  # Debug line
                response = handle_music_request(user_input)
                print(f"Chatbot: {response}")
                continue
            else:
                print(f"Debug: No song name extracted from: {user_input}")  # Debug line

        # Check if user wants to delete a file
        elif user_input.lower().startswith("delete file "):
            filename = user_input[12:].strip()
            result = delete_file(filename)
            print(f"Chatbot: {result}")

        # Check if user wants to create a file
        elif user_input.lower().startswith("create file "):
            filename = user_input[12:].strip()
            content = input("Enter file content (or leave blank for an empty file): ")
            result = create_file(filename, content)
            print(f"Chatbot: {result}")

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
