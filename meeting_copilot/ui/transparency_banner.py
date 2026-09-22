from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget

from meeting_copilot.ui.i18n import tr


class TransparencyBanner(QWidget):
    """A small always-on-top banner that stays visible while the copilot is
    active, so participants (e.g. via screen share) can see AI is in use."""

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(
            """
            QWidget { background-color: #b8860b; border-radius: 6px; }
            QLabel { color: white; font-weight: bold; padding: 6px; }
            QPushButton {
                background-color: white; color: #b8860b; font-weight: bold;
                border-radius: 4px; padding: 4px 10px;
            }
            QPushButton:hover { background-color: #f0f0f0; }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        self.label = QLabel()
        layout.addWidget(self.label)

        self.copy_btn = QPushButton()
        self.copy_btn.clicked.connect(self._copy_disclosure)
        layout.addWidget(self.copy_btn)

        self.retranslate_ui()
        self.adjustSize()
        self._reposition()

    def retranslate_ui(self) -> None:
        self.label.setText(tr("banner_text"))
        self.copy_btn.setText(tr("copy_disclosure_btn"))
        self.copy_btn.setToolTip(tr("copy_disclosure_tooltip"))
        self.adjustSize()
        self._reposition()

    def _copy_disclosure(self) -> None:
        QApplication.clipboard().setText(tr("disclosure_text"))

    def _reposition(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.center().x() - self.width() // 2
        y = geo.top() + 20
        self.move(x, y)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._reposition()
