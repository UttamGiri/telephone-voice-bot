"""WebSocket client to OpenAI Realtime API."""
import asyncio
import websockets
import json
import base64
import os
from dotenv import load_dotenv
from app.audio_utils import play_audio_chunk

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini-realtime-preview-2024-12-17")
WS_URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"


class OpenAIRealtimeClient:
    def __init__(self, output_websocket=None):
        self.ws = None
        self.output_websocket = output_websocket  # For forwarding audio to Amazon Connect
        self.audio_buffer = []

    async def connect(self):
        if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-xxxx"):
            raise ValueError("Invalid OPENAI_API_KEY. Please set a valid API key in .env")
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        self.ws = await websockets.connect(WS_URL, additional_headers=headers)
        print("Connected to OpenAI Realtime API")
        
        # Initialize session for conversation
        await self.ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": "You are a helpful assistant. Always speak in English only. Keep your responses short and concise - maximum 2 sentences. Be conversational and natural.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {"type": "server_vad", "threshold": 0.5, "prefix_padding_ms": 300, "silence_duration_ms": 500}
            }
        }))
        print("Session initialized for conversation")

    async def send_audio(self, audio_bytes):
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }))
        # Don't commit after every chunk - let server VAD handle turn detection

    async def receive_events(self):
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")
                
                if event_type == "session.created":
                    print("Session created")
                elif event_type == "session.updated":
                    print("Session updated")
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    print(f"You said: {transcript}")
                elif event_type == "conversation.item.created":
                    print("Conversation item created")
                elif event_type == "response.audio_transcript.delta":
                    print("AI speaking:", event.get("delta", ""), end="", flush=True)
                elif event_type == "response.audio_transcript.done":
                    print("\nAI finished speaking")
                elif event_type == "response.output_item.added":
                    print("Response item added")
                elif event_type == "response.output_audio_transcript.delta":
                    print("AI:", event.get("delta", ""), end="", flush=True)
                elif event_type == "response.output_audio_transcript.done":
                    print()
                elif event_type == "response.output_audio.delta":
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        # Forward to WebSocket client (Amazon Connect or test client)
                        if self.output_websocket:
                            try:
                                await self.output_websocket.send(audio_bytes)
                            except Exception as e:
                                print(f"Error forwarding audio: {e}")
                        # Only play locally if not in Docker (no audio devices in container)
                        try:
                            play_audio_chunk(audio_bytes)
                        except Exception:
                            pass  # Ignore audio playback errors (expected in Docker)
                elif event_type == "response.output_audio.done":
                    print("Audio done")
                elif event_type == "error":
                    print(f"Error from OpenAI: {event.get('error', {})}")
                else:
                    print(f"Event: {event_type}")
        except websockets.exceptions.ConnectionClosed:
            print("OpenAI WebSocket connection closed")
        except Exception as e:
            print(f"Error receiving events: {e}")
            import traceback
            traceback.print_exc()

