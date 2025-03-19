# J.A.R.V.I.S. Chatbot

A modern chatbot with Spotify integration, file management, and AI capabilities.

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm (comes with Node.js)
- Spotify Developer Account
- OpenAI API Key

## Setup Instructions

### 1. Install Python

#### On macOS:
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

#### On Windows:
Download and install Python from [python.org](https://www.python.org/downloads/)

#### On Linux:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Set Up Backend

```bash
# Create and activate virtual environment
python3 -m venv jarvis
source jarvis/bin/activate  # On Windows use: jarvis\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Set Up Frontend

```bash
# Navigate to frontend directory
cd chatbot-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Start the Application

1. Start the backend server (in one terminal):
```bash
# Make sure you're in the virtual environment
source jarvis/bin/activate  # On Windows use: jarvis\Scripts\activate

# Start the server
python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend server (in another terminal):
```bash
cd chatbot-frontend
npm run dev
```

3. Open your browser and navigate to `http://localhost:3000`

## Required API Keys

You need to set up the following API keys in your `.env` file:

1. **OpenAI API Key**
   - Get it from [OpenAI Platform](https://platform.openai.com/account/api-keys)
   - Format: `sk-...`

2. **Spotify API Keys**
   - Get them from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Required keys:
     - `SPOTIPY_CLIENT_ID`
     - `SPOTIPY_CLIENT_SECRET`
     - `SPOTIPY_REDIRECT_URI` (should be `http://127.0.0.1:8000/spotify/callback`)

## Features

- Chat with AI using OpenAI's GPT-3.5
- Play music, albums, and podcasts on Spotify
- Create and delete files
- Modern, responsive UI
- Real-time message updates

## Troubleshooting

1. **Python not found**
   - Make sure Python is installed and in your PATH
   - Try using `python3` instead of `python`

2. **Backend connection issues**
   - Ensure the FastAPI server is running
   - Check if port 8000 is available
   - Verify your API keys in `.env`

3. **Frontend issues**
   - Make sure all npm dependencies are installed
   - Check if port 3000 is available
   - Verify the backend URL in the frontend code

## Contributing

Feel free to submit issues and enhancement requests! 