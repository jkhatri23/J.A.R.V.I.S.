# J.A.R.V.I.S.
J.A.R.V.I.S. (Just A Rather Very Intelligent System) is an AI-powered chatbot designed to assist users by responding to various commands and inquiries. The chatbot can process natural language inputs, interact with external APIs, and perform tasks such as creating or deleting files. It is designed with a sleek user interface and provides real-time responses, making it a useful virtual assistant.

## Tech Stack:
### Frontend: 
- React(Next.js)
- Tailwind
- Typescript
### Backend:
- FastAPI
- Python

## Current State:
- Can delete files (mostly anywhere) by using "delete file NAME.extension"
- Can create files with "create file NAME.extension" AND can write in .txt files and .docx files
- Can play songs, albums, or podcasts on spotify and can add songs, albums, or podcasts to user's queue

## Setup Instructions:

### Prerequisites
- Docker and Docker Compose installed
- Spotify Developer Account with API credentials
- OpenAI API key
- Anthropic API key

### Configuration
1. Clone the repository:
   ```bash
   git clone https://github.com/jkhatri23/J.A.R.V.I.S..git
   cd J.A.R.V.I.S.
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your credentials:
   - Get your Spotify API credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Add your OpenAI API key
   - Add your Anthropic API key
   - Set your Docker user and group IDs (run `id` in terminal to get these values)

### Running the Application
1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Spotify Integration
- The first time you use Spotify features, you'll need to authenticate
- The application will redirect you to Spotify's login page
- After authentication, the token will be cached in the container
- You can control playback on any active Spotify device

### Troubleshooting
- If you encounter permission issues, ensure your Docker user/group IDs in `.env` match your system's values
- If Spotify authentication fails, check that your redirect URI matches the one in your Spotify Developer Dashboard
- For any other issues, check the container logs:
  ```bash
  docker-compose logs -f
  ```
