import logging
import warnings

import nemo.collections.asr as nemo_asr

from paathguide.audio_transcribe_tests.record_audio import AudioRecorder

# Force PyTorch to use CPU to avoid MPS warnings (optional)
# os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Suppress NeMo warnings
logging.getLogger("nemo_logger").setLevel(logging.ERROR)

# Suppress PyTorch MPS warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# Load the model from .nemo file


class PunjabiTranscriber:
    def __init__(self):
        self.asr_model = nemo_asr.models.EncDecCTCModelBPE.restore_from(
            "Conformer-CTC-BPE-Large.nemo"
        )

    def transcribe(self, recorder, duration=10):
        try:
            audio_file = recorder.record_audio(duration=duration)
            transcription = self.asr_model.transcribe(audio_file)  # type: ignore
            return transcription
        except Exception as e:
            print("Error during transcription:", e)
            return None
        finally:
            recorder.cleanup()


if __name__ == "__main__":
    recorder = AudioRecorder()
    transcriber = PunjabiTranscriber()
    output = transcriber.transcribe(recorder, duration=10)
    if output is not None and isinstance(output, list) and hasattr(output[0], "text"):
        print("Transcription:", output[0].text)
    else:
        print("Transcription failed or no text attribute in output.")

    # Cleanup temp file
    recorder.cleanup()
