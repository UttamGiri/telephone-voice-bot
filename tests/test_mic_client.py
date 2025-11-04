import asyncio
import websockets
import pyaudio

WEBSOCKET_URI = "ws://localhost:8765"

async def send_audio(ws, stream):
    try:
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            await ws.send(data)
            await asyncio.sleep(0.01)
    except Exception as e:
        print(f"Send error: {e}")

async def receive_audio(ws, output_stream):
    try:
        while True:
            response = await ws.recv()
            output_stream.write(response)
    except Exception as e:
        print(f"Receive error: {e}")

async def mic_test():
    async with websockets.connect(WEBSOCKET_URI) as ws:
        p = pyaudio.PyAudio()
        input_stream = p.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              input=True,
                              frames_per_buffer=1024)
        output_stream = p.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              output=True,
                              frames_per_buffer=1024)
        print("🎤 Ready for conversation! Speak naturally. Press Ctrl+C to stop")
        try:
            send_task = asyncio.create_task(send_audio(ws, input_stream))
            recv_task = asyncio.create_task(receive_audio(ws, output_stream))
            await asyncio.gather(send_task, recv_task)
        except KeyboardInterrupt:
            print("\n👋 Conversation ended")
            send_task.cancel()
            recv_task.cancel()
        finally:
            input_stream.stop_stream()
            input_stream.close()
            output_stream.stop_stream()
            output_stream.close()
            p.terminate()

asyncio.run(mic_test())

