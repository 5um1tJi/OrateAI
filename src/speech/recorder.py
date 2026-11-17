
import io
import wave


def get_audio_duration(audio_bytes: bytes) -> float:
    """
    Calculate the duration of a WAV audio recording.
    """

    with wave.open(io.BytesIO(audio_bytes), "rb") as audio:

        frames = audio.getnframes()
        sample_rate = audio.getframerate()

        if sample_rate <= 0:
            raise ValueError("Invalid audio sample rate.")

        duration = frames / float(sample_rate)

    return duration


def validate_audio_duration(
    duration: float,
    max_duration: int
) -> bool:
    """
    Check whether the recording is within the selected limit.
    """

    return duration <= max_duration
