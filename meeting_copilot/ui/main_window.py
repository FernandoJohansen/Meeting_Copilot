from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from meeting_copilot.audio.capture import AudioSourceCapture
from meeting_copilot.core.config import AppConfig, load_config, save_config
from meeting_copilot.core.session import TranscriptSegment, TranscriptStore
from meeting_copilot.llm.suggestions import SuggestionEngine
from meeting_copilot.llm.worker import SuggestionWorker
from meeting_copilot.stt.engine import WhisperTranscriber, detect_best_device
from meeting_copilot.stt.worker import TranscriptionWorker
from meeting_copilot.ui.i18n import set_language, tr
from meeting_copilot.ui.settings_dialog import PERFORMANCE_PRESETS, SettingsDialog
from meeting_copilot.ui.transparency_banner import TransparencyBanner


class ModelLoaderThread(QThread):
    ready = Signal(object)  # WhisperTranscriber
    error = Signal(str)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config

    def run(self) -> None:
        try:
            device, compute_type = self.config.whisper_device, self.config.whisper_compute_type
            if device == "auto":
                device, compute_type = detect_best_device()
            transcriber = WhisperTranscriber(
                model_size=self.config.whisper_model_size,
                device=device,
                compute_type=compute_type,
                language=self.config.language,
                cpu_threads=self.config.whisper_cpu_threads,
            )
            self.ready.emit(transcriber)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        set_language(self.config.ui_language)

        self.resize(1000, 650)

        self.transcript_store = TranscriptStore()
        self.transcript_store.segment_added.connect(self._on_segment_added)

        self.banner = TransparencyBanner()

        self.mic_capture: AudioSourceCapture | None = None
        self.system_capture: AudioSourceCapture | None = None
        self.transcription_worker: TranscriptionWorker | None = None
        self.suggestion_worker: SuggestionWorker | None = None
        self.model_loader: ModelLoaderThread | None = None
        self._running = False

        self._build_ui()
        self.retranslate_ui()

    # ---------------------------------------------------------------- UI ---
    def _build_ui(self) -> None:
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        self.start_stop_btn = QPushButton()
        self.start_stop_btn.clicked.connect(self._toggle_running)
        self.toolbar.addWidget(self.start_stop_btn)

        self.suggest_now_btn = QPushButton()
        self.suggest_now_btn.clicked.connect(self._trigger_suggestions_now)
        self.toolbar.addWidget(self.suggest_now_btn)

        self.settings_action = QAction(self)
        self.settings_action.triggered.connect(self._open_settings)
        self.toolbar.addAction(self.settings_action)

        self.toolbar.addSeparator()

        self.light_mode_btn = QPushButton()
        self.light_mode_btn.setCheckable(True)
        self.performance_mode_btn = QPushButton()
        self.performance_mode_btn.setCheckable(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.light_mode_btn)
        self.mode_group.addButton(self.performance_mode_btn)
        if self.config.performance_mode == "leve":
            self.light_mode_btn.setChecked(True)
        elif self.config.performance_mode == "desempenho":
            self.performance_mode_btn.setChecked(True)
        self.light_mode_btn.clicked.connect(lambda: self._apply_performance_mode("leve"))
        self.performance_mode_btn.clicked.connect(lambda: self._apply_performance_mode("desempenho"))
        self.toolbar.addWidget(self.light_mode_btn)
        self.toolbar.addWidget(self.performance_mode_btn)

        self.toolbar.addSeparator()

        self.lang_pt_btn = QPushButton("PT")
        self.lang_pt_btn.setCheckable(True)
        self.lang_en_btn = QPushButton("EN")
        self.lang_en_btn.setCheckable(True)
        self.lang_group = QButtonGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_group.addButton(self.lang_pt_btn)
        self.lang_group.addButton(self.lang_en_btn)
        if self.config.ui_language == "en":
            self.lang_en_btn.setChecked(True)
        else:
            self.lang_pt_btn.setChecked(True)
        self.lang_pt_btn.clicked.connect(lambda: self._apply_ui_language("pt"))
        self.lang_en_btn.clicked.connect(lambda: self._apply_ui_language("en"))
        self.toolbar.addWidget(self.lang_pt_btn)
        self.toolbar.addWidget(self.lang_en_btn)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        splitter = QSplitter()
        root_layout.addWidget(splitter)

        transcript_panel = QWidget()
        transcript_layout = QVBoxLayout(transcript_panel)
        self.transcript_title_label = QLabel()
        transcript_layout.addWidget(self.transcript_title_label)
        self.transcript_view = QTextEdit()
        self.transcript_view.setReadOnly(True)
        transcript_layout.addWidget(self.transcript_view)
        splitter.addWidget(transcript_panel)

        suggestions_panel = QWidget()
        suggestions_layout = QVBoxLayout(suggestions_panel)
        self.suggestions_title_label = QLabel()
        suggestions_layout.addWidget(self.suggestions_title_label)
        self.suggestions_list = QListWidget()
        suggestions_layout.addWidget(self.suggestions_list)
        splitter.addWidget(suggestions_panel)

        splitter.setSizes([650, 350])

        self.setStatusBar(QStatusBar())

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("app_title"))
        self.toolbar.setWindowTitle(tr("toolbar_title"))
        self.start_stop_btn.setText(tr("stop_meeting_btn") if self._running else tr("start_meeting_btn"))
        self.suggest_now_btn.setText(tr("suggest_now_btn"))
        self.settings_action.setText(tr("settings_action"))
        self.light_mode_btn.setText(tr("light_mode_btn"))
        self.performance_mode_btn.setText(tr("performance_mode_btn"))
        self.transcript_title_label.setText(tr("transcript_label"))
        self.suggestions_title_label.setText(tr("suggestions_label"))
        if not self._running:
            self.statusBar().showMessage(tr("ready_status"))

    # ------------------------------------------------------------ actions ---
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.updated_config()
            save_config(self.config)
            self.statusBar().showMessage(tr("settings_saved_status"), 4000)

    def _apply_performance_mode(self, mode: str) -> None:
        model_size, chunk_seconds, overlap_seconds, cpu_threads = PERFORMANCE_PRESETS[mode]
        self.config.whisper_model_size = model_size
        self.config.chunk_seconds = chunk_seconds
        self.config.overlap_seconds = overlap_seconds
        self.config.whisper_cpu_threads = cpu_threads
        self.config.performance_mode = mode
        save_config(self.config)

        status_key = "switching_to_light_status" if mode == "leve" else "switching_to_performance_status"
        self.statusBar().showMessage(tr(status_key), 4000)

        if self._running:
            self._stop_meeting()
            self._start_meeting()

    def _apply_ui_language(self, lang: str) -> None:
        set_language(lang)
        self.config.ui_language = lang
        save_config(self.config)
        self.retranslate_ui()
        self.banner.retranslate_ui()

    def _toggle_running(self) -> None:
        if self._running:
            self._stop_meeting()
        else:
            self._start_meeting()

    def _start_meeting(self) -> None:
        if self.config.mic_device_index is None and self.config.system_device_index is None:
            QMessageBox.warning(self, tr("no_audio_device_title"), tr("no_audio_device_msg"))
            return

        self.start_stop_btn.setEnabled(False)
        self.statusBar().showMessage(tr("loading_model_status"))

        self.model_loader = ModelLoaderThread(self.config, self)
        self.model_loader.ready.connect(self._on_model_ready)
        self.model_loader.error.connect(self._on_model_error)
        self.model_loader.start()

    def _on_model_error(self, message: str) -> None:
        self.start_stop_btn.setEnabled(True)
        self.statusBar().showMessage(tr("model_load_failed_status"))
        QMessageBox.critical(self, tr("error_loading_whisper_title"), message)

    def _on_model_ready(self, transcriber: WhisperTranscriber) -> None:
        self.transcription_worker = TranscriptionWorker(transcriber, self)
        self.transcription_worker.segment_ready.connect(self.transcript_store.add)
        self.transcription_worker.error.connect(lambda m: self.statusBar().showMessage(m, 6000))
        self.transcription_worker.start()

        you_label = tr("you_source")
        others_label = tr("others_source")

        if self.config.mic_device_index is not None:
            self.mic_capture = AudioSourceCapture(
                self.config.mic_device_index,
                you_label,
                self.config.chunk_seconds,
                self.config.overlap_seconds,
                parent=self,
            )
            self.mic_capture.chunk_ready.connect(
                lambda audio, ts: self.transcription_worker.submit(you_label, audio, ts)
            )
            self.mic_capture.error.connect(lambda m: self.statusBar().showMessage(m, 6000))
            self.mic_capture.start()

        if self.config.system_device_index is not None:
            self.system_capture = AudioSourceCapture(
                self.config.system_device_index,
                others_label,
                self.config.chunk_seconds,
                self.config.overlap_seconds,
                pulse_source_name=self.config.system_source_name,
                parent=self,
            )
            self.system_capture.chunk_ready.connect(
                lambda audio, ts: self.transcription_worker.submit(others_label, audio, ts)
            )
            self.system_capture.error.connect(lambda m: self.statusBar().showMessage(m, 6000))
            self.system_capture.start()

        engine: SuggestionEngine | None = None
        if self.config.llm_backend == "ollama":
            engine = SuggestionEngine(
                api_key="ollama",
                model=self.config.ollama_model,
                base_url=self.config.ollama_base_url,
            )
        elif self.config.openai_api_key:
            engine = SuggestionEngine(self.config.openai_api_key, self.config.openai_model)

        if engine is not None:
            self.suggestion_worker = SuggestionWorker(
                engine,
                self.transcript_store,
                self.config.suggestion_interval_seconds,
                self.config.suggestion_window_seconds,
                lambda: self.config.meeting_context,
                self,
            )
            self.suggestion_worker.suggestions_ready.connect(self._on_suggestions_ready)
            self.suggestion_worker.error.connect(lambda m: self.statusBar().showMessage(m, 6000))
            self.suggestion_worker.start()
        else:
            self.statusBar().showMessage(tr("no_openai_key_status"), 8000)

        self.banner.show()
        self._running = True
        self.start_stop_btn.setText(tr("stop_meeting_btn"))
        self.start_stop_btn.setEnabled(True)
        self.statusBar().showMessage(tr("meeting_running_status"))

    def _stop_meeting(self) -> None:
        for worker in (self.mic_capture, self.system_capture, self.transcription_worker, self.suggestion_worker):
            if worker is not None:
                worker.stop()
                worker.wait(3000)
        self.mic_capture = None
        self.system_capture = None
        self.transcription_worker = None
        self.suggestion_worker = None

        self.banner.hide()
        self._running = False
        self.start_stop_btn.setText(tr("start_meeting_btn"))
        self.statusBar().showMessage(tr("meeting_stopped_status"))

    def _trigger_suggestions_now(self) -> None:
        if self.suggestion_worker is not None:
            self.suggestion_worker.trigger_now()
        else:
            self.statusBar().showMessage(tr("suggestions_inactive_status"), 5000)

    # ------------------------------------------------------------- slots ---
    def _on_segment_added(self, segment: TranscriptSegment) -> None:
        self.transcript_view.append(segment.formatted())
        self.transcript_view.moveCursor(QTextCursor.MoveOperation.End)

    def _on_suggestions_ready(self, suggestions: list[str]) -> None:
        self.suggestions_list.clear()
        self.suggestions_list.addItems(suggestions)

    # ------------------------------------------------------------ window ---
    def closeEvent(self, event) -> None:  # noqa: N802
        if self._running:
            self._stop_meeting()
        self.banner.close()
        super().closeEvent(event)
