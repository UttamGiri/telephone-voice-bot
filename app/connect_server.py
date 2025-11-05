"""WebSocket server for Amazon Connect or local testing."""
import os
import asyncio
from dotenv import load_dotenv
from websockets.server import serve
from app.openai_client import OpenAIRealtimeClient

# Load environment variables
load_dotenv()

WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", 8765))


async def handler(websocket):
    print("New connection established")
    openai_client = OpenAIRealtimeClient(output_websocket=websocket)
    
    try:
        await openai_client.connect()
    except Exception as e:
        print(f"Failed to connect to OpenAI: {e}")
        await websocket.close()
        return

    receive_task = asyncio.create_task(openai_client.receive_events())

    try:
        async for message in websocket:
            # Fix 4: Handle both binary (audio) and text messages
            if isinstance(message, bytes):
                # Binary message - audio data from Amazon Connect / Twilio / test client
                await openai_client.send_audio(message)
            else:
                # Text message - could be Twilio ping, status, etc.
                print(f"📨 Received text message: {message[:100]}...")
                # Optionally handle text messages if needed
    except Exception as e:
        print(f"Error: {e}")
    finally:
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
        if openai_client.ws:
            await openai_client.ws.close()


async def main():
    server = await serve(handler, WEBSOCKET_HOST, WEBSOCKET_PORT)
    print(f"WebSocket server running at ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())

