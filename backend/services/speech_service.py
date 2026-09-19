import os
import io
import wave
import tempfile

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from faster_whisper import WhisperModel
from piper import PiperVoice


# ============================================================
# DOMAIN CORRECTIONS
# ============================================================

WHISPER_CORRECTIONS = {
    # reschedule variants
    "re-schedule": "reschedule",
    "re schedule": "reschedule",
    "reschedul": "reschedule",
    "reshedul": "reschedule",
    "reshuffle": "reschedule",
    "re-schedul": "reschedule",
    "schedule again": "reschedule",

    # cancel variants
    "cancle": "cancel",
    "canceled": "cancel",
    "cancelled": "cancel",

    # badminton
    "bad mitten": "badminton",
    "bad minton": "badminton",
    "badmenton": "badminton",
    "bat minton": "badminton",

    # tennis / football / turf
    "tenis": "tennis",
    "foot ball": "football",
    "footbol": "football",
    "terf": "turf",

    # booking IDs
    "b k g": "BKG",
    "bk g": "BKG",
    "booking id": "BKG",
}


def _apply_corrections(text: str) -> str:
    """Apply domain-specific corrections to Whisper output."""
    if not text:
        return text
    lowered = text.lower()
    for wrong, right in WHISPER_CORRECTIONS.items():
        lowered = lowered.replace(wrong, right.lower())
    return lowered


# ============================================================
# CONFIGURATION
# ============================================================

WHISPER_MODEL_SIZE = "small"  # tiny | base | small | medium | large-v3
WHISPER_DEVICE = "cpu"         # "cpu" or "cuda"

PIPER_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "voices",
    "en_US-lessac-medium.onnx"
)


# ============================================================
# LOAD MODELS (once at import)
# ============================================================

print("[SPEECH] Loading Whisper model...")
_whisper_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device=WHISPER_DEVICE,
    compute_type="int8"
)

print("[SPEECH] Loading Piper voice...")
_piper_voice = PiperVoice.load(PIPER_MODEL_PATH)


# ============================================================
# SPEECH → TEXT
# ============================================================

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    from pydub import AudioSegment
    from pydub.effects import normalize

    tmp_in_path = None
    wav_path = None

    try:
        # Save raw audio
        with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(filename)[1],
            delete=False
        ) as tmp_in:
            tmp_in.write(audio_bytes)
            tmp_in_path = tmp_in.name

        # Preprocess: 16kHz mono, normalized, high-pass filtered
        wav_path = tmp_in_path + ".wav"
        audio = AudioSegment.from_file(tmp_in_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio = normalize(audio)
        audio = audio.high_pass_filter(80)
        audio.export(wav_path, format="wav")

        # Transcribe with all optimizations
        segments, info = _whisper_model.transcribe(
            wav_path,
            beam_size=8,
            language="en",
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                threshold=0.5,
            ),
            initial_prompt=(
                "This is a turf booking request. "
                "Common words: badminton, football, tennis, turf, court, "
                "booking, reschedule, cancel, equipment, membership, "
                "BKG booking ID, tomorrow, today, AM, PM."
            ),
        )

        text = " ".join(seg.text for seg in segments).strip()
        print(f"[STT] Raw: {text!r}")
        text = _apply_corrections(text)
        print(f"[STT] Corrected: {text!r}")

        return {
            "success": True,
            "text": text,
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
        }

    except Exception as e:
        print(f"[STT ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error_code": "TRANSCRIPTION_FAILED",
            "message": str(e),
        }

    finally:
        for p in (tmp_in_path, wav_path):
            if p:
                try:
                    os.remove(p)
                except Exception:
                    pass
# ============================================================
# TEXT → SPEECH
# ============================================================

def synthesize_speech(text: str) -> bytes:
    """
    Convert text into a WAV audio blob using Piper.
    """
    output_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        with wave.open(output_path, "wb") as wav_file:
            _piper_voice.synthesize_wav(text, wav_file)

        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        return audio_bytes

    finally:
        if output_path:
            try:
                os.remove(output_path)
            except Exception:
                pass