from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional

import sounddevice as sd

_LOOPBACK_HINTS = ("monitor", "loopback", "what u hear", "stereo mix")
_PULSE_PASSTHROUGH_NAMES = ("pulse", "pipewire")


@dataclass
class InputDevice:
    index: int
    name: str
    hostapi: str
    max_input_channels: int
    default_samplerate: float
    is_probable_loopback: bool

    @property
    def label(self) -> str:
        tag = "  [loopback/sistema]" if self.is_probable_loopback else ""
        return f"{self.name} ({self.hostapi}){tag}"


@dataclass
class PulseMonitorSource:
    """A PipeWire/PulseAudio monitor source (captures 'what you hear' from a
    specific sink), discovered via `pactl`. PortAudio/ALSA cannot address
    these directly by name, so they are captured through the generic
    'pulse'/'pipewire' ALSA passthrough device using the PULSE_SOURCE
    environment variable at stream-open time (see capture.py)."""

    name: str
    description: str

    @property
    def label(self) -> str:
        return f"{self.description}  ({self.name})"


def list_input_devices() -> list[InputDevice]:
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    result: list[InputDevice] = []
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) <= 0:
            continue
        name = dev.get("name", f"device {idx}")
        hostapi_name = hostapis[dev["hostapi"]]["name"] if dev.get("hostapi") is not None else ""
        lowered = name.lower()
        is_loopback = any(hint in lowered for hint in _LOOPBACK_HINTS)
        result.append(
            InputDevice(
                index=idx,
                name=name,
                hostapi=hostapi_name,
                max_input_channels=dev["max_input_channels"],
                default_samplerate=dev.get("default_samplerate", 44100.0),
                is_probable_loopback=is_loopback,
            )
        )
    return result


def default_mic_device(devices: Optional[list[InputDevice]] = None) -> Optional[int]:
    devices = devices if devices is not None else list_input_devices()
    non_loopback = [d for d in devices if not d.is_probable_loopback and d.name.lower() not in _PULSE_PASSTHROUGH_NAMES]
    if non_loopback:
        return non_loopback[0].index
    return devices[0].index if devices else None


def find_pulse_passthrough_device(devices: Optional[list[InputDevice]] = None) -> Optional[int]:
    """Finds the generic ALSA 'pulse' or 'pipewire' device that PortAudio
    exposes to reach the PulseAudio/PipeWire server (used to target a
    specific monitor source via PULSE_SOURCE)."""
    devices = devices if devices is not None else list_input_devices()
    by_name = {d.name.lower(): d for d in devices}
    for candidate in _PULSE_PASSTHROUGH_NAMES:
        if candidate in by_name:
            return by_name[candidate].index
    return None


def list_pulse_monitor_sources() -> list[PulseMonitorSource]:
    """Lists monitor sources ('what you hear' from each sink) via `pactl`.
    Returns an empty list if pactl is unavailable (e.g. non-Linux)."""
    try:
        short = subprocess.run(
            ["pactl", "list", "sources", "short"], capture_output=True, text=True, timeout=5, check=True
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []

    monitors: list[PulseMonitorSource] = []
    for line in short.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[1].strip()
        if not name.endswith(".monitor"):
            continue
        monitors.append(PulseMonitorSource(name=name, description=name))
    return monitors


def default_system_source(monitors: Optional[list[PulseMonitorSource]] = None) -> Optional[str]:
    monitors = monitors if monitors is not None else list_pulse_monitor_sources()
    if not monitors:
        return None
    preferred = [m for m in monitors if "output" in m.name and "monitor" in m.name]
    return (preferred or monitors)[0].name
