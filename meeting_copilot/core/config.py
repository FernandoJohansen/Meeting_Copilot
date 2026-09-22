from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from platformdirs import user_config_dir

APP_NAME = "MeetingCopilot"


def config_path() -> Path:
    return Path(user_config_dir(APP_NAME)) / "config.json"


@dataclass
class AppConfig:
    llm_backend: str = "openai"  # "openai" ou "ollama"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_cpu_threads: int = 0  # 0 = deixa a ctranslate2 usar todos os núcleos
    language: str = "pt"

    mic_device_index: Optional[int] = None
    system_device_index: Optional[int] = None  # ALSA 'pulse'/'pipewire' passthrough device
    system_source_name: Optional[str] = None  # PipeWire/PulseAudio monitor source (via pactl)

    chunk_seconds: float = 8.0
    overlap_seconds: float = 0.5

    suggestion_interval_seconds: float = 25.0
    suggestion_window_seconds: float = 180.0

    meeting_context: str = ""

    ui_language: str = "pt"  # idioma da interface: "pt" ou "en"
    performance_mode: str = "equilibrado"  # "leve", "equilibrado" ou "desempenho"

    def to_dict(self) -> dict:
        return asdict(self)


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppConfig()
    defaults = AppConfig().to_dict()
    defaults.update({k: v for k, v in data.items() if k in defaults})
    return AppConfig(**defaults)


def save_config(cfg: AppConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
