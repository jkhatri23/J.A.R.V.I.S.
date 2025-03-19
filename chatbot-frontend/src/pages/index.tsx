import { useState, useEffect } from "react";
import { Orbitron } from 'next/font/google';

const orbitron = Orbitron({
  subsets: ['latin'],
  weight: ['500', '700'],
});

// Add this function at the top of the file, before the Home component
function extractSongName(text: string): { name: string; type: 'song' | 'album' | 'podcast' } {
  const lowerText = text.toLowerCase().trim();
  
  // Check for podcast requests first
  if (lowerText.includes('podcast')) {
    // Try to match "[action] podcast [name]" pattern
    const podcastPattern = /(?:play|queue|add)\s+(?:the\s+)?podcast\s+([^.!?]+)/;
    const podcastMatch = lowerText.match(podcastPattern);
    
    if (podcastMatch) {
      return { name: podcastMatch[1].trim(), type: 'podcast' };
    }

    // Try to match "[action] [podcast name]" when podcast is mentioned in the text
    const podcastNamePattern = /(?:play|queue|add)\s+([^.!?]+?)(?:\s+podcast)?/;
    const podcastNameMatch = lowerText.match(podcastNamePattern);
    
    if (podcastNameMatch) {
      return { name: podcastNameMatch[1].trim(), type: 'podcast' };
    }
  }
  
  // Check for album requests
  if (lowerText.includes('album')) {
    // Try to match "[action] album [name] by [artist]" pattern
    const albumByPattern = /(?:play|queue|add)\s+(?:the\s+)?album\s+([^.!?]+?)\s+by\s+([^.!?]+)/;
    const albumMatch = lowerText.match(albumByPattern);
    
    if (albumMatch) {
      const [, album, artist] = albumMatch;
      return { name: `${album.trim()} ${artist.trim()}`, type: 'album' };
    }
    
    // Try to match "[action] album [name]" pattern
    const albumPattern = /(?:play|queue|add)\s+(?:the\s+)?album\s+([^.!?]+)/;
    const simpleAlbumMatch = lowerText.match(albumPattern);
    
    if (simpleAlbumMatch) {
      return { name: simpleAlbumMatch[1].trim(), type: 'album' };
    }

    // Try to match "add album [name] to queue" pattern
    const queueAlbumPattern = /add\s+(?:the\s+)?album\s+([^.!?]+)\s+to\s+queue/;
    const queueAlbumMatch = lowerText.match(queueAlbumPattern);
    
    if (queueAlbumMatch) {
      return { name: queueAlbumMatch[1].trim(), type: 'album' };
    }
  }
  
  // Try to match "[action] [song] by [artist]" pattern
  const actionByPattern = /(?:play|queue|add)\s+([^.!?]+?)\s+by\s+([^.!?]+)/;
  const match = lowerText.match(actionByPattern);
  
  if (match) {
    const [, song, artist] = match;
    return { name: `${song.trim()} ${artist.trim()}`, type: 'song' };
  }
  
  // Try to match "[action] [song]" pattern
  const actionPattern = /(?:play|queue|add)\s+([^.!?]+)/;
  const actionMatch = lowerText.match(actionPattern);
  
  if (actionMatch) {
    return { name: actionMatch[1].trim(), type: 'song' };
  }
  
  // Try to match "add [song] to queue" pattern
  const queuePattern = /add\s+([^.!?]+)\s+to\s+queue/;
  const queueMatch = lowerText.match(queuePattern);
  
  if (queueMatch) {
    return { name: queueMatch[1].trim(), type: 'song' };
  }
  
  return { name: text.trim(), type: 'song' };
}

export default function Home() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [createFileMode, setCreateFileMode] = useState<{ filename: string } | null>(null);
  const [fileContent, setFileContent] = useState("");

  // Add message listener for Spotify OAuth callback
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data === 'spotify-auth-success') {
        setMessages(prev => [...prev, {
          role: "bot",
          content: "Successfully authenticated with Spotify! You can now play music."
        }]);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);

    let response;

    try {
      // Check for music requests
      if (input.toLowerCase().includes("play") || input.toLowerCase().includes("queue") || 
          input.toLowerCase().includes("song") || input.toLowerCase().includes("music") || 
          input.toLowerCase().includes("spotify") || input.toLowerCase().includes("album") ||
          input.toLowerCase().includes("podcast")) {
        const { name, type } = extractSongName(input);
        
        // Determine if it's a queue request
        const isQueueRequest = input.toLowerCase().includes("queue") || 
                             input.toLowerCase().includes("add to queue");
        
        let endpoint;
        if (type === 'podcast') {
          endpoint = isQueueRequest ? "queue-podcast" : "play-podcast";
        } else if (type === 'album') {
          endpoint = isQueueRequest ? "queue-album" : "play-album";
        } else {
          endpoint = isQueueRequest ? "queue-song" : "play-song";
        }
        
        response = await fetch(`http://127.0.0.1:8000/spotify/${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ song_name: name }),
        });

        const data = await response.json();
        
        // Handle different response types
        let botMessage;
        if (data.error) {
          if (data.error.includes("User not logged in")) {
            // Open the authorization URL in a new window
            const authUrl = "http://127.0.0.1:8000/spotify/authorize";
            window.open(authUrl, "_blank");
            botMessage = { 
              role: "bot", 
              content: "Please authorize the app in the new window that opened. After authorizing, you'll be redirected back to the app." 
            };
          } else {
            botMessage = { role: "bot", content: data.error };
          }
        } else if (data.success) {
          botMessage = { role: "bot", content: data.success };
        } else {
          botMessage = { role: "bot", content: "Sorry, I couldn't process that request." };
        }
        
        setMessages((prev) => [...prev, botMessage]);
        return;
      }
      // Check for file deletion
      else if (input.toLowerCase().startsWith("delete file ")) {
        const filename = input.slice(12).trim();
        response = await fetch("http://127.0.0.1:8000/delete-file", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename }),
        });
      } 
      // Check for file creation
      else if (input.toLowerCase().startsWith("create file ")) {
        const filename = input.slice(12).trim();
        setCreateFileMode({ filename });
        return; // stop here to wait for file content input
      } 
      // Default to chat
      else {
        try {
          response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: input }),
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        } catch (error) {
          console.error("Error connecting to backend:", error);
          setMessages((prev) => [...prev, {
            role: "bot",
            content: "I can't connect to the backend server. Please make sure the FastAPI server is running by executing 'python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000' in your terminal."
          }]);
          return;
        }
      }

      const data = await response.json();
      
      // Handle different response types
      let botMessage;
      if (data.error) {
        botMessage = { role: "bot", content: data.error };
      } else if (data.success) {
        botMessage = { role: "bot", content: data.success };
      } else if (data.response) {
        botMessage = { role: "bot", content: data.response };
      } else {
        botMessage = { role: "bot", content: "Sorry, I couldn't process that request." };
      }
      
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = { role: "bot", content: "Sorry, I encountered an error. Please make sure the backend server is running." };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInput("");
  };

  const submitFileContent = async () => {
    if (!createFileMode) return;

    const { filename } = createFileMode;

    const response = await fetch("http://127.0.0.1:8000/create-file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, content: fileContent }),
    });

    const data = await response.json();
    const botMessage = { role: "bot", content: data.response };
    setMessages((prev) => [...prev, botMessage]);
    setCreateFileMode(null);
    setFileContent("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (createFileMode) {
        submitFileContent();
      } else {
        sendMessage();
      }
    }
  };

  return (
   <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-black text-white">
      <h1 className={`text-4xl mb-6 text-blue-100 ${orbitron.className} glowing-text`}>J.A.R.V.I.S</h1>
      <div className="w-full max-w-2xl border border-blue-300 rounded-lg p-6 h-96 overflow-y-auto bg-zinc-900 shadow-lg space-y-4 custom-scrollbar">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <p
              className={`p-4 rounded-lg max-w-max ${
                msg.role === "user"
                  ? "bg-blue-400 text-right text-white"
                  : "bg-blue-500 text-left text-white"
              }`}
            >
              {msg.content}
            </p>
          </div>
        ))}

        {/* Inline file content input */}
        {createFileMode && (
          <div className="flex flex-col space-y-2">
            <p className="text-sm text-blue-300">
              Enter content for <span className="font-bold">{createFileMode.filename}</span>:
            </p>
            <textarea
              rows={4}
              className="bg-zinc-800 border border-blue-400 rounded-lg p-3 text-white focus:outline-none"
              placeholder="Type file content here..."
              value={fileContent}
              onChange={(e) => setFileContent(e.target.value)}
            ></textarea>
            <div className="flex justify-end space-x-2">
              <button
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
                onClick={() => {
                  setCreateFileMode(null);
                  setFileContent("");
                }}
              >
                Cancel
              </button>
              <button
                className="bg-blue-400 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                onClick={submitFileContent}
              >
                Create File
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Wrapper for input + button */}
      {!createFileMode && (
        <div className="flex w-full max-w-2xl mt-6 group focus-within:ring-2 focus-within:ring-blue-500 rounded-lg">
          <input
            className="flex-1 bg-zinc-800 border border-blue-300 p-4 rounded-l-lg placeholder-gray-600 text-white focus:outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
          />
          <button
            className="bg-blue-400 hover:bg-blue-700 text-white px-6 py-3 rounded-r-lg"
            onClick={sendMessage}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}
