
import os
import tempfile

from functools import lru_cache
from faster_whisper import WhisperModel


@lru_cache(maxsize=1)
def load_whisper_model():
    """
    Load Whisper only once and reuse it.
    """

    model = WhisperModel(
        "base.en",
        device="cpu",
        compute_type="int8"
    )

    return model


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Convert recorded audio bytes into English text.
    """

    if not audio_bytes:
        raise ValueError("No audio was provided.")

    model = load_whisper_model()

    temp_path = None

    try:

        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:

            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        # Run speech recognition
        segments, info = model.transcribe(
            temp_path,
            language="en",
            beam_size=5,
            vad_filter=True
        )

        # Consume the generator and collect recognized text
        transcript = " ".join(
            segment.text.strip()
            for segment in segments
        )

        if not transcript.strip():
            raise ValueError(
                "Whisper could not detect any speech. "
                "Please try recording again."
            )

        return transcript.strip()

    finally:

        # Remove temporary audio file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
