# Telephone Voice Bot with OpenAI Realtime API

A real-time voice assistant using Twilio Voice, FastAPI, and OpenAI's Realtime API for Speech-to-Speech (S2S) conversations. The AI speaks as **Uttam Giri** with dynamic resume context injection.

## Architecture

```
Twilio Phone Call → FastAPI WebSocket → OpenAI Realtime API → Audio Response → Twilio → Caller
```

## Features

- **Real-time Speech-to-Speech**: Direct audio streaming without intermediate text conversion
- **Twilio Media Streams Integration**: Seamless phone call handling
- **OpenAI Realtime API**: GPT Realtime model for low-latency conversations
- **Dynamic Resume Context**: Automatically searches and injects relevant resume information
- **FastAPI Framework**: Modern, async Python web framework
- **Persona-Driven**: AI speaks as "Uttam Giri" in first person

## Prerequisites

- Python 3.9+ (tested with 3.9.13)
- Twilio account with Voice-enabled phone number
- OpenAI account with Realtime API access
- OpenAI API Key
- (Optional) ngrok for local testing

## Project Structure

```
telephone-voice-bot/
├── app/
│   ├── __init__.py
│   ├── resume_context.py        # Resume context management
│   ├── llm_manager.py           # Resume search and context injection
│
├── main.py                      # FastAPI server - Main entry point
├── .env                         # Environment variables
├── Dockerfile                   # Containerization
├── requirements.txt
└── README.md
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

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-realtime
VOICE=cove
TEMPERATURE=0.8
PORT=5050
```

**Note:** 
- `OPENAI_MODEL` should be `gpt-realtime` for the new Realtime API
- `VOICE` can be `alloy`, `echo`, `shimmer`, or `cove` (default: `cove` for Uttam Giri persona)
- `TEMPERATURE` controls response randomness (0.0-1.0)

### 3. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 5050
```

Or use Python directly:

```bash
python main.py
```

You should see:
```
🚀 Starting Twilio Voice AI Assistant
📞 OpenAI Model: gpt-realtime
🎤 Voice: cove
🌐 Server running on port 5050
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5050
```

## Twilio Setup

### 1. Expose Your Server (Local Development)

Use ngrok to expose your local server:

```bash
ngrok http 5050
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.app`)

### 2. Configure Twilio Phone Number

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on your Voice-enabled number
4. Under "Voice & Fax", set **A CALL COMES IN** webhook to:
   ```
   https://your-ngrok-url.ngrok.app/incoming-call
   ```
5. Save the configuration

### 3. Test Your Setup

1. Make sure your server is running
2. Ensure ngrok is active
3. Call your Twilio phone number
4. You should hear: "Please wait while we connect your call..."
5. Then: "OK, you can start talking!"
6. The AI will greet you: "Hey, I am Uttam speaking. How can I help you today?"
7. Start talking - you'll hear real-time responses!

## How It Works

### 1. Incoming Call Flow

1. Twilio receives call → sends webhook to `/incoming-call`
2. FastAPI returns TwiML → instructs Twilio to connect to `/media-stream` WebSocket
3. Twilio connects to WebSocket → bidirectional audio streaming begins

### 2. OpenAI Realtime Integration

1. FastAPI establishes WebSocket connection to OpenAI Realtime API
2. Sends `session.update` with Uttam Giri persona and instructions
3. Sends initial greeting via `response.create`
4. Proxies audio between Twilio and OpenAI in real-time

### 3. Resume Context Injection

- When user speaks, OpenAI transcribes audio
- System detects if question is about "Uttam" or related topics
- Searches `resume_full.txt` for relevant information
- Injects matching context into LLM via `response.create`
- AI responds with accurate, personalized information

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *required* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-realtime` | OpenAI Realtime model |
| `VOICE` | `cove` | AI voice (alloy, echo, shimmer, cove) |
| `TEMPERATURE` | `0.8` | Response randomness (0.0-1.0) |
| `PORT` | `5050` | Server port |

### System Message

The AI persona is configured in `main.py`:

```python
SYSTEM_MESSAGE = (
    "You are Uttam Giri. Speak in first person as Uttam himself. "
    "Say: 'Hey, I am Uttam speaking.' "
    f"Your background: {get_short_resume()}\n\n"
    "Stay concise (1–2 sentences). Always respond in English. "
    "If unsure, say 'I don't have that information right now.'"
)
```

## Docker Deployment

### Build Image

```bash
docker build -t telephone-voice-bot .
```

### Run Container

```bash
docker run -d \
  --name voice-bot \
  -p 5050:5050 \
  --env-file .env \
  telephone-voice-bot
```

**Note:** The Dockerfile should use `CMD ["python", "main.py"]` or `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"]` for FastAPI deployment.


## Troubleshooting

### Common Issues

1. **"Missing OpenAI API key"**
   - Ensure `.env` file exists with `OPENAI_API_KEY` set
   - Check that `load_dotenv()` is called

2. **"WebSocket connection failed"**
   - Verify OpenAI API key is valid
   - Check that you have Realtime API access
   - Ensure model is set to `gpt-realtime`

3. **"Twilio can't connect"**
   - Verify ngrok is running and URL is correct
   - Check Twilio webhook configuration
   - Ensure server is accessible from internet

4. **"No audio response"**
   - Check server logs for `response.output_audio.delta` events
   - Verify `streamSid` is set correctly
   - Ensure audio format is `audio/pcmu` (Twilio compatible)

5. **"Resume context not working"**
   - Verify `resume_full.txt` exists in project root
   - Check logs for "Searching resume for..." messages
   - Ensure transcript detection is working

### Debug Logging

The server logs important events. Look for:
- `📞 Client connected to media stream`
- `✅ Session updated successfully`
- `🎤 User said: [transcript]`
- `📄 Searching resume for: [query]`
- `🎵 Sent audio chunk: X bytes`
- `✅ Audio response completed`

## API Endpoints

- `GET /` - Health check endpoint
- `POST /incoming-call` - Twilio webhook for incoming calls
- `WebSocket /media-stream` - Twilio Media Stream connection


## Resources

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Twilio Media Streams Documentation](https://www.twilio.com/docs/voice/twiml/stream)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Twilio Python Helper Library](https://www.twilio.com/docs/libraries/python)

## License

MIT

## Author

Uttam Giri
