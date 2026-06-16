"""
PustakaDesk — main.py

Entry point utama aplikasi PustakaDesk.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database.db_buku import DatabaseBuku


APP_NAME = "PustakaDesk"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "Kelompok 9"

BASE_DIR = Path(__file__).resolve().parent
STYLE_DIR = BASE_DIR / "style"


def load_stylesheet(app: QApplication, dark_mode: bool = False) -> None:
    """Memuat stylesheet tema terang atau gelap ke aplikasi."""
    filename = "style_dark.qss" if dark_mode else "style.qss"
    stylesheet_path = STYLE_DIR / filename

    try:
        stylesheet = stylesheet_path.read_text(encoding="utf-8")
        app.setStyleSheet(stylesheet)
    except OSError as error:
        print(
            f"[PERINGATAN] Stylesheet tidak dapat dimuat: "
            f"{stylesheet_path}\n{error}"
        )


def configure_application(app: QApplication) -> None:
    """Mengatur identitas aplikasi dan fallback font."""
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)

    # Beberapa kombinasi Windows dan PySide6 dapat menghasilkan
    # point size font tidak valid (-1).
    app_font = app.font()

    if app_font.pointSize() <= 0:
        app_font.setPointSize(10)
        app.setFont(app_font)


def initialize_database() -> DatabaseBuku:
    """Membuat koneksi, migrasi, dan memperbarui status peminjaman."""
    database = DatabaseBuku()
    database.initialize()
    database.update_status_terlambat()

    return database


def main() -> int:
    """Menjalankan aplikasi PustakaDesk."""
    print(
        f"[{APP_NAME} {APP_VERSION}] "
        f"Menjalankan: {Path(__file__).resolve()}"
    )

    app = QApplication(sys.argv)
    configure_application(app)

    database = initialize_database()
    load_stylesheet(app, dark_mode=False)

    # Import lokal membantu menghindari circular import pada navigasi login.
    from ui.ui_login import LoginWindow

    login_window = LoginWindow(
        database,
        app,
        load_stylesheet,
    )
    login_window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())