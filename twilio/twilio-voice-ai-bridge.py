# twilio-voice-ai-bridge.py
#
# A minimal Twilio → AI Voice bridge:
# - Twilio sends HTTP webhook (via ngrok) to /voice
# - Flask returns TwiML to tell Twilio to stream audio to your public URL (TWILIO_STREAM_URL)
# - Flask can also notify your local AI WebSocket (WEBSOCKET_URL)
# - Works locally with ngrok and easily deploys to AWS Lambda later

from flask import Flask, Response, request
import os, json
import websocket  # for internal LLM signaling (optional)

app = Flask(__name__)

# 🧩 Configuration
# 1️⃣ TWILIO_STREAM_URL: public URL (WSS) that Twilio connects to for streaming audio
TWILIO_STREAM_URL = os.getenv("TWILIO_STREAM_URL", "wss://gyroidal-closely-alverta.ngrok-free.dev")

# 2️⃣ WEBSOCKET_URL: your local LLM or AI WebSocket (internal, no ngrok needed)
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8765")

# 3️⃣ Flask server port (default 5050)
PORT = int(os.getenv("PORT", 5050))


@app.route("/", methods=["GET"])
def home():
    """Root endpoint for Twilio heartbeat - prevents HTTP 400"""
    return "Twilio Voice-AI Bridge OK", 200

@app.route("/voice", methods=["POST"])
def voice():
    """Handles inbound call webhook from Twilio"""
    caller = request.form.get("From")
    print(f"📞 Incoming call from {caller}")
    print(f"➡️  Twilio will stream audio to: {TWILIO_STREAM_URL}")

    # Optional: Notify your local AI/LLM WebSocket
    try:
        ws = websocket.create_connection(WEBSOCKET_URL)
        ws.send(json.dumps({"event": "incoming_call", "from": caller}))
        ws.close()
        print(f"🤖 Notified local LLM at {WEBSOCKET_URL}")
    except Exception as e:
        print(f"⚠️ Could not reach local WebSocket {WEBSOCKET_URL}: {e}")

    # Respond to Twilio: tell it to stream audio to TWILIO_STREAM_URL
    xml = f"""
    <Response>
        <Say voice="Polly.Matthew">Hello, connecting you to the AI agent.</Say>
        <Connect>
            <Stream url="{TWILIO_STREAM_URL}" />
        </Connect>
    </Response>
    """
    return Response(xml.strip(), mimetype="text/xml")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "twilio_stream_url": TWILIO_STREAM_URL,
        "local_websocket_url": WEBSOCKET_URL
    }


if __name__ == "__main__":
    print("🚀 Starting Twilio Voice → AI Bridge")
    print(f"🌐 Twilio audio stream (public): {TWILIO_STREAM_URL}")
    print(f"🤖 Local AI WebSocket: {WEBSOCKET_URL}")
    print(f"🧭 Running on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
