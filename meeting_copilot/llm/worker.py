from __future__ import annotations

import time
from typing import Callable

from PySide6.QtCore import QThread, Signal

from meeting_copilot.core.session import TranscriptStore
from meeting_copilot.llm.suggestions import SuggestionEngine


class SuggestionWorker(QThread):
    suggestions_ready = Signal(list)  # list[str]
    error = Signal(str)

    def __init__(
        self,
        engine: SuggestionEngine,
        transcript_store: TranscriptStore,
        interval_seconds: float,
        window_seconds: float,
        context_provider: Callable[[], str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.transcript_store = transcript_store
        self.interval_seconds = interval_seconds
        self.window_seconds = window_seconds
        self.context_provider = context_provider
        self._running = False
        self._force_next = False
        self._last_text_seen = ""

    def trigger_now(self) -> None:
        self._force_next = True

    def run(self) -> None:
        self._running = True
        last_run = 0.0
        while self._running:
            time.sleep(1.0)
            now = time.time()
            due = (now - last_run) >= self.interval_seconds
            if not (due or self._force_next):
                continue

            window_text = self.transcript_store.window_text(self.window_seconds)
            if not window_text.strip():
                continue
            if window_text == self._last_text_seen and not self._force_next:
                continue

            self._force_next = False
            last_run = now
            self._last_text_seen = window_text
            try:
                suggestions = self.engine.generate(window_text, self.context_provider())
                self.suggestions_ready.emit(suggestions)
            except Exception as exc:
                self.error.emit(f"Erro ao gerar sugestões: {exc}")

    def stop(self) -> None:
        self._running = False
