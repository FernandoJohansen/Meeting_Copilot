from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from meeting_copilot.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Meeting Copilot")
    app.setOrganizationName("MeetingCopilot")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
