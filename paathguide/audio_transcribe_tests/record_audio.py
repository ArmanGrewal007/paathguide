## Record audio and save to a temp file
import os
import pyaudio
import tempfile
import wave

class AudioRecorder:
  def __init__(self) -> None:
    self.temp_file = None

  def record_audio(self, duration=5, sample_rate=16000):
    """Record audio from microphone and return temp file path"""
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                   channels=channels,
                   rate=sample_rate,
                   input=True,
                   frames_per_buffer=chunk)

    print(f"Recording for {duration} seconds...")
    frames = []

    for i in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save to temporary file with automatic cleanup
    self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    wf = wave.open(self.temp_file.name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    return self.temp_file.name

  def cleanup(self):
    """Clean up temporary files"""
    if self.temp_file and os.path.exists(self.temp_file.name):
        os.unlink(self.temp_file.name)
        print(f"Cleaned up temporary file: {self.temp_file.name}")
