from __future__ import annotations

import contextlib
import os
import queue
import time
from typing import Optional

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QThread, Signal

TARGET_SAMPLERATE = 16000


def _resample_linear(block: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    if src_rate == dst_rate or block.size == 0:
        return block
    duration = block.size / src_rate
    dst_len = max(1, int(round(duration * dst_rate)))
    src_x = np.linspace(0.0, duration, num=block.size, endpoint=False)
    dst_x = np.linspace(0.0, duration, num=dst_len, endpoint=False)
    return np.interp(dst_x, src_x, block).astype(np.float32)


@contextlib.contextmanager
def _pulse_source_override(source_name: Optional[str]):
    """Temporarily sets PULSE_SOURCE so the generic ALSA 'pulse'/'pipewire'
    passthrough device connects to a specific monitor source. PortAudio has
    no direct way to address individual PulseAudio/PipeWire sources by name,
    but the ALSA pulse plugin reads this env var when the stream is opened."""
    if not source_name:
        yield
        return
    previous = os.environ.get("PULSE_SOURCE")
    os.environ["PULSE_SOURCE"] = source_name
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PULSE_SOURCE", None)
        else:
            os.environ["PULSE_SOURCE"] = previous


class AudioSourceCapture(QThread):
    """Captures audio from one input device and emits fixed-length mono
    16kHz float32 chunks (with a small overlap for context continuity)."""

    chunk_ready = Signal(object, float)  # (np.ndarray, timestamp)
    error = Signal(str)

    def __init__(
        self,
        device_index: int,
        source_label: str,
        chunk_seconds: float = 6.0,
        overlap_seconds: float = 1.0,
        pulse_source_name: Optional[str] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.device_index = device_index
        self.source_label = source_label
        self.chunk_seconds = chunk_seconds
        self.overlap_seconds = overlap_seconds
        self.pulse_source_name = pulse_source_name
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue()
        self._running = False
        self._capture_rate = TARGET_SAMPLERATE
        self._need_resample = False

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: D401
        if status:
            pass  # xruns are common and non-fatal; ignore
        self._queue.put(indata[:, 0].copy())

    def _open_stream(self) -> sd.InputStream:
        try:
            return sd.InputStream(
                samplerate=TARGET_SAMPLERATE,
                channels=1,
                dtype="float32",
                device=self.device_index,
                callback=self._callback,
                blocksize=int(TARGET_SAMPLERATE * 0.5),
            )
        except Exception:
            info = sd.query_devices(self.device_index)
            self._capture_rate = int(info["default_samplerate"])
            self._need_resample = True
            return sd.InputStream(
                samplerate=self._capture_rate,
                channels=1,
                dtype="float32",
                device=self.device_index,
                callback=self._callback,
                blocksize=int(self._capture_rate * 0.5),
            )

    def run(self) -> None:
        self._running = True
        try:
            with _pulse_source_override(self.pulse_source_name):
                stream = self._open_stream()
        except Exception as exc:  # device unavailable, permissions, etc.
            self.error.emit(f"Falha ao abrir dispositivo de áudio '{self.source_label}': {exc}")
            return

        chunk_frames = int(self.chunk_seconds * TARGET_SAMPLERATE)
        overlap_frames = int(self.overlap_seconds * TARGET_SAMPLERATE)
        buf = np.zeros(0, dtype=np.float32)

        with stream:
            while self._running:
                try:
                    block = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                if self._need_resample:
                    block = _resample_linear(block, self._capture_rate, TARGET_SAMPLERATE)
                buf = np.concatenate([buf, block])
                if buf.size >= chunk_frames:
                    emit_chunk = buf[:chunk_frames]
                    buf = buf[chunk_frames - overlap_frames :] if overlap_frames > 0 else np.zeros(0, dtype=np.float32)
                    self.chunk_ready.emit(emit_chunk, time.time())

    def stop(self) -> None:
        self._running = False
