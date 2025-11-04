# Telephone Voice Bot

A real-time voice bot that connects Amazon Connect to OpenAI's Realtime GPT-4o-mini API using WebSockets for bidirectional audio streaming.

## Architecture

```
Amazon Connect → WebSocket Server → OpenAI Realtime API → Audio Playback
```

## Features

- Real-time microphone capture and audio streaming
- WebSocket server for handling Amazon Connect connections
- OpenAI Realtime GPT-4o-mini integration for voice conversations
- Bidirectional audio: captures user speech and plays AI responses
- Local testing support with microphone client
- Docker containerization for easy deployment

## Project Structure

```
voice-bot/
├── app/
│   ├── __init__.py
│   ├── audio_utils.py           # Mic capture + playback
│   ├── openai_client.py         # OpenAI Realtime WebSocket client
│   ├── connect_server.py        # WebSocket server handling Amazon Connect
│   ├── llm_pipeline.py          # Optional: placeholder for text processing
│
├── tests/
│   ├── test_mic_client.py       # Local microphone test client
│
├── .env                         # API keys, AWS region, model info
├── Dockerfile                   # Containerization for deployment
├── requirements.txt
├── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** On macOS, you may need to install PortAudio first:
```bash
brew install portaudio
```

On Linux (Ubuntu/Debian):
```bash
sudo apt-get install portaudio19-dev
```

### 2. Configure Environment Variables

Edit `.env` file with your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini-realtime-preview-2024-12-17
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
DEBUG=true
```

**Important:** Do not commit `.env` to version control. It's already in `.gitignore`.

### 3. Run the WebSocket Server

```bash
python app/connect_server.py
```

The server will start on `ws://0.0.0.0:8765`

### 4. Test Locally (Optional)

In a separate terminal, run the microphone test client:

```bash
python tests/test_mic_client.py
```

This will:
- Connect to the local WebSocket server
- Capture audio from your microphone
- Send it to OpenAI Realtime API
- Play back the AI's audio responses

## Usage

### Local Testing

1. Start the server:
   ```bash
   python app/connect_server.py
   ```

2. Run the test client:
   ```bash
   python tests/test_mic_client.py
   ```

3. Speak into your microphone and listen for AI responses.

### Amazon Connect Integration

The WebSocket server is ready to accept connections from Amazon Connect. Configure your Connect contact flow to:

1. Connect to your WebSocket server endpoint
2. Stream audio in PCM16 format (16kHz, mono)
3. Receive audio responses from the server

The server expects:
- **Input:** Raw PCM16 audio bytes (16kHz, mono, 16-bit)
- **Output:** Raw PCM16 audio bytes (same format)

## Docker Deployment

### Build the Image

```bash
docker build -t voice-bot .
```

### Run the Container

```bash
docker run -p 8765:8765 --env-file .env voice-bot
```

**Note:** For production, ensure your `.env` file has the correct API keys and configuration.

## Configuration

### Audio Settings

- **Sample Rate:** 16,000 Hz
- **Channels:** 1 (mono)
- **Format:** PCM16 (16-bit signed integers)
- **Chunk Size:** 1024 samples (default)

### WebSocket Settings

- **Host:** `0.0.0.0` (listen on all interfaces)
- **Port:** `8765` (default)

Both can be configured via `.env` file.

## Troubleshooting

### PyAudio Installation Issues

If you encounter issues installing PyAudio:

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

### WebSocket Connection Errors

- Ensure the server is running before connecting
- Check firewall settings for port 8765
- Verify `WEBSOCKET_HOST` and `WEBSOCKET_PORT` in `.env`

### OpenAI API Errors

- Verify your `OPENAI_API_KEY` is correct in `.env`
- Check that you have access to the Realtime API
- Ensure your API key has sufficient credits

## Development

### Adding Features

- **Text Processing:** Extend `app/llm_pipeline.py` for additional text processing
- **Audio Processing:** Modify `app/audio_utils.py` for audio enhancement/filtering
- **Connection Handling:** Update `app/connect_server.py` for advanced connection management

## License

This project is provided as-is for development and testing purposes.

ONE TERMINAL

docker build -t telephone-voice-bot .
docker run -it --rm -p 8765:8765 --env-file .env telephone-voice-bot


OTHER TERMINAL

python3 tests/test_mic_client.py 


# telephone-voice-bot
