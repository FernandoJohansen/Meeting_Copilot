from __future__ import annotations

import numpy as np
from faster_whisper import WhisperModel


def detect_best_device() -> tuple[str, str]:
    """Returns (device, compute_type). Falls back to CPU if no CUDA GPU."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


class WhisperTranscriber:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "pt",
        cpu_threads: int = 0,
    ) -> None:
        # cpu_threads=0 lets ctranslate2 auto-detect all available cores;
        # pass a positive value to cap usage and leave headroom for the UI
        # thread and the OS on constrained machines.
        self.model = WhisperModel(
            model_size, device=device, compute_type=compute_type, cpu_threads=cpu_threads
        )
        self.language = None if language in ("", "auto") else language

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        segments, _info = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
