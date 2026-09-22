from __future__ import annotations

import queue

import numpy as np
from PySide6.QtCore import QThread, Signal

from meeting_copilot.core.session import TranscriptSegment
from meeting_copilot.stt.engine import WhisperTranscriber


class TranscriptionWorker(QThread):
    """Serially transcribes audio chunks from any number of sources using a
    single shared Whisper model instance (faster-whisper is not safe to call
    concurrently from multiple threads on one model)."""

    segment_ready = Signal(object)  # TranscriptSegment
    error = Signal(str)

    def __init__(self, transcriber: WhisperTranscriber, parent=None) -> None:
        super().__init__(parent)
        self.transcriber = transcriber
        self._queue: "queue.Queue[tuple[str, np.ndarray, float]]" = queue.Queue()
        self._running = False

    def submit(self, source_label: str, audio: np.ndarray, timestamp: float) -> None:
        self._queue.put((source_label, audio, timestamp))

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                source, audio, ts = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                text = self.transcriber.transcribe(audio)
            except Exception as exc:
                self.error.emit(f"Erro na transcrição ({source}): {exc}")
                continue
            if text:
                self.segment_ready.emit(TranscriptSegment(source=source, text=text, timestamp=ts))

    def stop(self) -> None:
        self._running = False
