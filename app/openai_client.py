"""WebSocket client to OpenAI Realtime API."""
import asyncio
import websockets
import json
import base64
import os
from dotenv import load_dotenv
from app.audio_utils import play_audio_chunk
from app.resume_context import get_short_resume
from app.llm_manager import should_load_full_resume, inject_full_resume, is_uttam_question, get_context_for_query

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
        
        # Initialize session with résumé context - PERSONA MODE
        resume_summary = get_short_resume()
        
        # Step 1: Keep session persona SHORT and identity-focused only
        # This anchors the voice identity - proven pattern for production Realtime
        session_persona = (
            f"You are Uttam Giri. Speak in first person as Uttam himself and say hey I am Uttam speaking"
            f"Your background: {resume_summary}"
        )
        
        # Step 2: Behavioral instructions (concise, for session-level)
        behavioral_rules = (
            "Stay concise (1-2 sentences). Always answer in English only. "
            "If unsure, say 'I don't have that information right now.'"
        )
        
        # Combine persona + behavioral rules for session
        persona_instructions = f"{session_persona}\n\n{behavioral_rules}"

        
        # Debug: Show what's being sent
        print("\n" + "="*60)
        print("📋 SETTING PERSONA IN SESSION.UPDATE:")
        print("="*60)
        print(f"Persona: {persona_instructions[:150]}...")
        print("="*60 + "\n")
        
        # Step 1: Update session with persona BEFORE any audio/responses
        # IMPORTANT: Send this ONCE at session start - do NOT re-send during the session
        # This sets the permanent persona that persists for all responses
        session_config = {
            "type": "session.update",
            "session": {
                "type": "realtime",  # Required: must be "realtime" for audio calls
                "model": MODEL,  # Required: specify model in session update
                "instructions": persona_instructions  # Persona set here - persists for all responses
            }
        }
        
        await self.ws.send(json.dumps(session_config))
        print("✅ Session persona set - Uttam Giri persona is now active for all responses")
        
        # Wait briefly for session to be updated before sending any audio
        await asyncio.sleep(0.3)
        
        # Send initial greeting to keep the call open and streaming
        greeting_event = {
            "type": "response.create",
            "response": {
                "modalities": ["audio"],
                "instructions": "Hey, I am Uttam speaking. How can I help you today?",
                "voice": "cove"
            }
        }
        await self.ws.send(json.dumps(greeting_event))
        print("🎤 Sent initial greeting to OpenAI for Twilio stream")

    async def send_audio(self, audio_bytes):
        # Fix 3: Ensure audio_bytes is actually bytes
        if isinstance(audio_bytes, str):
            audio_bytes = audio_bytes.encode('latin-1')  # Preserve binary data
        if not isinstance(audio_bytes, bytes):
            audio_bytes = bytes(audio_bytes)
        
        # Encode to base64 and send as text JSON to OpenAI Realtime API
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }))
        # Don't commit after every chunk - let server VAD handle turn detection
    
    async def inject_context_for_transcript(self, transcript: str):
        """Inject context from resume_full.txt into LLM for the given transcript."""
        if not transcript or not self.ws:
            return
        
        print(f"\n📄 Searching resume_full.txt for: '{transcript}'")
        
        # Step 1: Search resume_full.txt for matching information
        context = get_context_for_query(transcript)
        
        if context:
            print(f"✅ Found matching info ({len(context)} chars)")
            print(f"📋 Context preview: {context[:300]}...")
            
            # Step 2: Inject matching information into LLM
            context_prompt = (
                f"User asked: {transcript}\n\n"
                f"Use ONLY this matching information from Uttam Giri's resume to answer:\n{context}\n\n"
                f"Answer in first person as Uttam Giri. Keep it concise (1-2 sentences). Always in English."
            )
            
            try:
                await self.ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio"],
                        "instructions": context_prompt,
                        "voice": "cove"  # Voice belongs in response.create, not session.update
                    }
                }))
                print("✅ Matching resume information injected into LLM")
            except Exception as e:
                print(f"⚠️  Error injecting context: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️  No matching information found in resume_full.txt")

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
                    print(f"\n🎤 You said: {transcript}")
                    
                    # Amazon Connect flow: ALWAYS search resume_full.txt for EVERY transcript
                    # This ensures resume context is always available to LLM
                    if transcript and len(transcript.strip()) > 2:
                        await self.inject_context_for_transcript(transcript)
                    else:
                        print("ℹ️  Empty or too short transcript - skipping context injection")
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
                        print(f"🎵 Audio delta received: {len(audio_bytes)} bytes")  # Debug: verify audio is coming
                        
                        # Forward to WebSocket client (Amazon Connect or test client)
                        if self.output_websocket:
                            try:
                                # Fix 2: Ensure we're sending bytes, not strings
                                if isinstance(audio_bytes, str):
                                    audio_bytes = audio_bytes.encode("utf-8")
                                # Ensure it's bytes
                                if not isinstance(audio_bytes, bytes):
                                    audio_bytes = bytes(audio_bytes)
                                await self.output_websocket.send(audio_bytes)
                            except Exception as e:
                                print(f"Error forwarding audio: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Only play locally if not in Docker (no audio devices in container)
                        try:
                            play_audio_chunk(audio_bytes)
                        except Exception:
                            pass  # Ignore audio playback errors (expected in Docker)
                elif event_type == "response.output_audio.done":
                    print("✅ response.output_audio.done - Audio response completed")
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

