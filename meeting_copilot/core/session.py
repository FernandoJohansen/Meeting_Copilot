from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


@dataclass
class TranscriptSegment:
    source: str  # e.g. "Você" or "Outros"
    text: str
    timestamp: float  # time.time() when the segment finished

    def formatted(self) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        return f"[{ts}] {self.source}: {self.text}"


class TranscriptStore(QObject):
    """Thread-safe rolling store of transcript segments.

    Segments may be added from worker threads; ``segment_added`` is safe to
    connect to a GUI slot because Qt auto-queues the signal across threads.
    """

    segment_added = Signal(object)  # TranscriptSegment

    def __init__(self) -> None:
        super().__init__()
        self._segments: list[TranscriptSegment] = []
        self._lock = threading.Lock()

    def add(self, segment: TranscriptSegment) -> None:
        with self._lock:
            self._segments.append(segment)
        self.segment_added.emit(segment)

    def all_segments(self) -> list[TranscriptSegment]:
        with self._lock:
            return list(self._segments)

    def window(self, seconds: float) -> list[TranscriptSegment]:
        cutoff = time.time() - seconds
        with self._lock:
            return [s for s in self._segments if s.timestamp >= cutoff]

    def window_text(self, seconds: float) -> str:
        return "\n".join(s.formatted() for s in self.window(seconds))

    def full_text(self) -> str:
        with self._lock:
            return "\n".join(s.formatted() for s in self._segments)

    def clear(self) -> None:
        with self._lock:
            self._segments.clear()
