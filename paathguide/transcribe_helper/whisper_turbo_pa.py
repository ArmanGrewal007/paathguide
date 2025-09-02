import whisper

from paathguide.transcribe_helper.record_audio import AudioRecorder


def transcribe_from_microphone(audio_recorder, duration=10, model_size="medium", language="pa"):
    """Record audio and transcribe with automatic cleanup"""
    model = whisper.load_model(model_size)
    audio_file = None

    try:
        # Record audio
        audio_file = audio_recorder.record_audio(duration=duration)

        # Transcribe with debugging info
        result = model.transcribe(audio_file, language=language, fp16=False)

        # Debug: Print detected language and confidence
        print(f"Detected language: {result.get('language', 'unknown')}")
        print(f"Raw result keys: {result.keys()}")
        print(f"Text repr: {repr(result['text'])}")

        return result["text"]

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        audio_recorder.cleanup()


# Usage
if __name__ == "__main__":
    try:
        audio_recorder = AudioRecorder()
        transcribe_from_microphone(audio_recorder, duration=10, model_size="turbo", language="pa")
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
