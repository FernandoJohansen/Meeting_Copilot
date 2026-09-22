from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from meeting_copilot.audio.devices import (
    find_pulse_passthrough_device,
    list_input_devices,
    list_pulse_monitor_sources,
)
from meeting_copilot.core.config import AppConfig
from meeting_copilot.ui.i18n import tr

WHISPER_MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

# (modelo, chunk_seconds, overlap_seconds, cpu_threads) — cpu_threads=0 -> automático (todos os núcleos)
PERFORMANCE_PRESETS = {
    "leve": ("tiny", 10.0, 0.3, 2),
    "equilibrado": ("base", 8.0, 0.5, 0),
    "desempenho": ("small", 5.0, 1.0, 0),
}


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(480)
        self._config = config

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.engine_combo = QComboBox()
        self.engine_combo.addItem(tr("llm_backend_openai"), userData="openai")
        self.engine_combo.addItem(tr("llm_backend_ollama"), userData="ollama")
        idx = self.engine_combo.findData(config.llm_backend)
        self.engine_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow(tr("llm_backend_label"), self.engine_combo)

        self.api_key_edit = QLineEdit(config.openai_api_key)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        show_key_btn = QPushButton(tr("show_password_btn"))
        show_key_btn.setCheckable(True)
        show_key_btn.toggled.connect(
            lambda checked: self.api_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_row = QVBoxLayout()
        key_row.addWidget(self.api_key_edit)
        key_row.addWidget(show_key_btn)
        form.addRow(tr("api_key_label"), key_row)

        self.ollama_url_edit = QLineEdit(config.ollama_base_url)
        self.ollama_url_edit.setToolTip(tr("ollama_url_tooltip"))
        form.addRow(tr("ollama_url_label"), self.ollama_url_edit)

        self.ollama_model_edit = QLineEdit(config.ollama_model)
        self.ollama_model_edit.setToolTip(tr("ollama_model_tooltip"))
        form.addRow(tr("ollama_model_label"), self.ollama_model_edit)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel(tr("performance_profile_label")))
        for key, label_key in (
            ("leve", "preset_light_label"),
            ("equilibrado", "preset_balanced_label"),
            ("desempenho", "preset_performance_label"),
        ):
            btn = QPushButton(tr(label_key))
            btn.clicked.connect(lambda _checked, k=key: self._apply_preset(k))
            preset_row.addWidget(btn)
        layout.addLayout(preset_row)
        layout.addWidget(QLabel(tr("preset_info_label")))

        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(WHISPER_MODEL_SIZES)
        self.model_size_combo.setCurrentText(config.whisper_model_size)
        form.addRow(tr("whisper_model_label"), self.model_size_combo)

        self.language_combo = QComboBox()
        for code, label_key in (("auto", "lang_auto"), ("pt", "lang_pt"), ("en", "lang_en"), ("es", "lang_es")):
            self.language_combo.addItem(tr(label_key), userData=code)
        idx = self.language_combo.findData(config.language)
        self.language_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow(tr("transcription_language_label"), self.language_combo)

        self.mic_combo = QComboBox()
        for dev in list_input_devices():
            self.mic_combo.addItem(dev.label, userData=dev.index)
        self._select_combo_data(self.mic_combo, config.mic_device_index)
        form.addRow(tr("mic_label"), self.mic_combo)

        self.system_combo = QComboBox()
        self.system_combo.addItem(tr("system_audio_none_option"), userData=None)
        monitors = list_pulse_monitor_sources()
        for monitor in monitors:
            self.system_combo.addItem(monitor.label, userData=monitor.name)
        self._select_combo_data(self.system_combo, config.system_source_name)
        if not monitors:
            self.system_combo.setToolTip(tr("system_audio_no_monitor_tooltip"))
        form.addRow(tr("system_audio_label"), self.system_combo)
        self._pulse_passthrough_index = find_pulse_passthrough_device()
        if monitors and self._pulse_passthrough_index is None:
            self.system_combo.setEnabled(False)
            self.system_combo.setToolTip(tr("system_audio_no_passthrough_tooltip"))

        self.chunk_spin = QDoubleSpinBox()
        self.chunk_spin.setRange(3, 30)
        self.chunk_spin.setSuffix(" s")
        self.chunk_spin.setToolTip(tr("chunk_seconds_tooltip"))
        self.chunk_spin.setValue(config.chunk_seconds)
        form.addRow(tr("chunk_seconds_label"), self.chunk_spin)

        self.overlap_spin = QDoubleSpinBox()
        self.overlap_spin.setRange(0, 3)
        self.overlap_spin.setSuffix(" s")
        self.overlap_spin.setToolTip(tr("overlap_tooltip"))
        self.overlap_spin.setValue(config.overlap_seconds)
        form.addRow(tr("overlap_label"), self.overlap_spin)

        self.cpu_threads_spin = QSpinBox()
        self.cpu_threads_spin.setRange(0, 32)
        self.cpu_threads_spin.setSpecialValueText(tr("cpu_threads_auto_text"))
        self.cpu_threads_spin.setToolTip(tr("cpu_threads_tooltip"))
        self.cpu_threads_spin.setValue(config.whisper_cpu_threads)
        form.addRow(tr("cpu_threads_label"), self.cpu_threads_spin)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(5, 300)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setValue(config.suggestion_interval_seconds)
        form.addRow(tr("suggestion_interval_label"), self.interval_spin)

        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(15, 900)
        self.window_spin.setSuffix(" s")
        self.window_spin.setValue(config.suggestion_window_seconds)
        form.addRow(tr("suggestion_window_label"), self.window_spin)

        self.context_edit = QPlainTextEdit(config.meeting_context)
        self.context_edit.setPlaceholderText(tr("meeting_context_placeholder"))
        self.context_edit.setFixedHeight(80)
        form.addRow(tr("meeting_context_label"), self.context_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _select_combo_data(combo: QComboBox, value) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _apply_preset(self, key: str) -> None:
        model_size, chunk_seconds, overlap_seconds, cpu_threads = PERFORMANCE_PRESETS[key]
        self.model_size_combo.setCurrentText(model_size)
        self.chunk_spin.setValue(chunk_seconds)
        self.overlap_spin.setValue(overlap_seconds)
        self.cpu_threads_spin.setValue(cpu_threads)

    def updated_config(self) -> AppConfig:
        cfg = self._config
        cfg.llm_backend = self.engine_combo.currentData()
        cfg.openai_api_key = self.api_key_edit.text().strip()
        cfg.ollama_base_url = self.ollama_url_edit.text().strip()
        cfg.ollama_model = self.ollama_model_edit.text().strip()
        cfg.whisper_model_size = self.model_size_combo.currentText()
        cfg.language = self.language_combo.currentData()
        cfg.mic_device_index = self.mic_combo.currentData()
        cfg.system_source_name = self.system_combo.currentData()
        cfg.system_device_index = self._pulse_passthrough_index if cfg.system_source_name else None
        cfg.chunk_seconds = self.chunk_spin.value()
        cfg.overlap_seconds = min(self.overlap_spin.value(), max(self.chunk_spin.value() - 1, 0))
        cfg.whisper_cpu_threads = self.cpu_threads_spin.value()
        cfg.suggestion_interval_seconds = self.interval_spin.value()
        cfg.suggestion_window_seconds = self.window_spin.value()
        cfg.meeting_context = self.context_edit.toPlainText().strip()
        return cfg
