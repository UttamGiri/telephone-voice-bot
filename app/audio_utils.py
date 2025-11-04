"""Handles microphone capture and playback."""
import pyaudio

SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16

# Global audio instance for playback
_audio = None
_output_stream = None

def get_audio():
    """Get or create global PyAudio instance"""
    global _audio
    if _audio is None:
        _audio = pyaudio.PyAudio()
    return _audio

def get_output_stream():
    """Get or create global output stream for real-time playback"""
    global _output_stream
    if _output_stream is None:
        p = get_audio()
        _output_stream = p.open(format=FORMAT, channels=CHANNELS,
                               rate=SAMPLE_RATE, output=True)
    return _output_stream

def play_audio_chunk(audio_bytes):
    """Play PCM16 audio chunk immediately using persistent stream"""
    stream = get_output_stream()
    stream.write(audio_bytes)

def cleanup_audio():
    """Clean up audio resources"""
    global _output_stream, _audio
    if _output_stream:
        _output_stream.stop_stream()
        _output_stream.close()
        _output_stream = None
    if _audio:
        _audio.terminate()
        _audio = None


