"""
PustakaDesk — ui_member.py
Halaman anggota: beranda, katalog, pinjaman, riwayat, dan profil.
"""

import os
import shutil
import uuid
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QScrollArea, QGridLayout, QMessageBox, QComboBox,
    QFormLayout, QFileDialog, QDialog, QDialogButtonBox, QDateEdit,
    QCalendarWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QPixmap

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROFILE_DIR = os.path.join(PROJECT_ROOT, "assets", "profiles")
MEMBER_UI_BUILD = "v23"


def _row_to_dict(row):
    try:
        return dict(row)
    except Exception:
        return row if isinstance(row, dict) else {}


def _member_id(user):
    user = _row_to_dict(user)
    return user.get("id_user") or user.get("id")


def _project_path(path_value: str) -> str:
    if not path_value:
        return ""
    if os.path.isabs(str(path_value)):
        return str(path_value)
    return os.path.join(PROJECT_ROOT, str(path_value))


def _cover_label(image_path: str, width: int = 76, height: int = 104) -> QLabel:
    label = QLabel("Buku")
    label.setObjectName("book_cover")
    label.setAlignment(Qt.AlignCenter)
    label.setFixedSize(width, height)

    path = _project_path(image_path)
    if path and os.path.exists(path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setText("")
    return label


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


def _format_member_date(value) -> str:
    """Format tanggal ISO menjadi ringkas dan mudah dibaca anggota."""
    if not value:
        return "-"
    try:
        parsed = date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return str(value)

    months = (
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
        "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
    )
    return f"{parsed.day:02d} {months[parsed.month - 1]} {parsed.year}"


def _format_rupiah(value) -> str:
    try:
        amount = int(float(value or 0))
    except (TypeError, ValueError):
        amount = 0
    return f"Rp {amount:,}".replace(",", ".")


def _loan_info_item(label_text: str, value_text: str, value_object: str = "loan_info_value"):
    """Buat pasangan label/nilai tanpa kotak agar detail kartu tetap ringan."""
    wrapper = QWidget()
    wrapper.setObjectName("loan_info_item")
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)

    label = QLabel(label_text)
    label.setObjectName("loan_info_label")
    value = QLabel(value_text)
    value.setObjectName(value_object)

    layout.addWidget(label)
    layout.addWidget(value)
    return wrapper


def _section_header(title_text: str, subtitle_text: str = ""):
    """Header halaman. Subtitle opsional agar tampilan tidak terasa penuh teks."""
    header = QFrame()
    header.setObjectName("member_page_header")
    layout = QVBoxLayout(header)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(4)

    title = QLabel(title_text)
    title.setObjectName("member_page_title")
    layout.addWidget(title)

    if subtitle_text:
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("member_page_subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

    return header


def _copy_profile_image(source_path: str) -> str:
    os.makedirs(PROFILE_DIR, exist_ok=True)
    ext = os.path.splitext(source_path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        ext = ".png"
    filename = f"profile_{uuid.uuid4().hex[:12]}{ext}"
    dest_abs = os.path.join(PROFILE_DIR, filename)
    shutil.copy2(source_path, dest_abs)
    return os.path.join("assets", "profiles", filename).replace("\\", "/")


def _apply_profile_picture(label: QLabel, image_path: str, fallback_text: str, size: int = 96):
    label.setText(fallback_text)
    label.setPixmap(QPixmap())
    label.setFixedSize(size, size)
    path = _project_path(image_path)
    if path and os.path.exists(path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            label.setText("")


class ClickableBookCard(QFrame):
    """Kartu buku yang dapat diklik tanpa mengubah tampilannya menjadi tombol."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class CalendarOnlyDateEdit(QPushButton):
    """Pemilih tanggal berbentuk tombol penuh yang hanya membuka kalender."""

    dateChanged = Signal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date = QDate.currentDate()
        self._minimum_date = QDate.currentDate().addYears(-1)
        self._maximum_date = QDate.currentDate().addYears(5)
        self._display_format = "dd MMM yyyy"

        self.setObjectName("calendar_date_selector")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(58)
        self.setToolTip("Klik seluruh kotak ini untuk memilih tanggal")
        self.clicked.connect(self._open_calendar)

        self._popup = QDialog(self, Qt.Popup)
        self._popup.setObjectName("calendar_popup_dialog")
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(10, 10, 10, 10)
        popup_layout.setSpacing(8)

        self._calendar = QCalendarWidget(self._popup)
        self._calendar.setGridVisible(False)
        self._calendar.setMinimumSize(390, 270)
        self._calendar.clicked.connect(self._select_date)
        popup_layout.addWidget(self._calendar)

        self._refresh_text()

    def setDisplayFormat(self, display_format: str):
        self._display_format = display_format or "dd MMM yyyy"
        self._refresh_text()

    def setMinimumDate(self, value: QDate):
        self._minimum_date = QDate(value)
        self._calendar.setMinimumDate(value)
        if self._date < value:
            self.setDate(value)

    def setMaximumDate(self, value: QDate):
        self._maximum_date = QDate(value)
        self._calendar.setMaximumDate(value)
        if self._date > value:
            self.setDate(value)

    def setDate(self, value: QDate):
        bounded = QDate(value)
        if bounded < self._minimum_date:
            bounded = QDate(self._minimum_date)
        if bounded > self._maximum_date:
            bounded = QDate(self._maximum_date)

        changed = bounded != self._date
        self._date = bounded
        self._calendar.setSelectedDate(bounded)
        self._refresh_text()
        if changed:
            self.dateChanged.emit(QDate(self._date))

    def date(self) -> QDate:
        return QDate(self._date)

    def calendarWidget(self) -> QCalendarWidget:
        return self._calendar

    def _refresh_text(self):
        formatted = self._date.toString(self._display_format)
        self.setText(f"📅  {formatted}    •    Klik untuk memilih tanggal")

    def _select_date(self, selected: QDate):
        self.setDate(selected)
        self._popup.accept()

    def _open_calendar(self):
        self._calendar.setSelectedDate(self._date)
        popup_width = max(410, self.width())
        self._popup.resize(popup_width, 310)

        position = self.mapToGlobal(self.rect().bottomLeft())
        screen = QApplication.screenAt(position)
        if screen is not None:
            area = screen.availableGeometry()
            x = min(max(position.x(), area.left()), area.right() - popup_width + 1)
            y = position.y()
            if y + self._popup.height() > area.bottom():
                y = self.mapToGlobal(self.rect().topLeft()).y() - self._popup.height()
            y = max(area.top(), y)
            self._popup.move(x, y)
        else:
            self._popup.move(position)

        self._popup.exec()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._open_calendar()
            event.accept()
            return
        super().keyPressEvent(event)


class BorrowConfirmationDialog(QDialog):
    """Pilih batas pengembalian dan konfirmasi peminjaman."""

    DIRECT_DAYS = 7
    MAX_DAYS = 30

    def __init__(self, book: dict, tanggal_pinjam: date, tanggal_kembali: date, parent=None):
        super().__init__(parent)
        self.book = _row_to_dict(book)
        self.tanggal_pinjam = tanggal_pinjam
        self.setWindowTitle("Konfirmasi Peminjaman")
        self.setObjectName("clean_dialog")
        self.setMinimumWidth(480)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("Konfirmasi Peminjaman")
        title.setObjectName("detail_dialog_title")
        note = QLabel("Pilih batas pengembalian sesuai kebutuhan.")
        note.setObjectName("detail_hint")
        root.addWidget(title)
        root.addWidget(note)

        summary = QFrame()
        summary.setObjectName("detail_description_box")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        summary_layout.setSpacing(7)

        book_title = QLabel(str(self.book.get("judul", "-")))
        book_title.setObjectName("detail_book_title")
        book_title.setWordWrap(True)
        author = QLabel(f"{self.book.get('penulis', '-')} • {self.book.get('kategori', '-')}")
        author.setObjectName("book_author")
        author.setWordWrap(True)
        borrowed_at = QLabel(f"Tanggal pinjam: {tanggal_pinjam.isoformat()}")
        borrowed_at.setObjectName("detail_description_text")
        summary_layout.addWidget(book_title)
        summary_layout.addWidget(author)
        summary_layout.addWidget(borrowed_at)
        root.addWidget(summary)

        date_label = QLabel("Batas pengembalian")
        date_label.setObjectName("calendar_date_label")
        root.addWidget(date_label)

        self.return_date = CalendarOnlyDateEdit()
        calendar = self.return_date.calendarWidget()
        calendar.setMinimumSize(390, 270)
        calendar.setGridVisible(False)
        self.return_date.setDisplayFormat("dd MMM yyyy")
        self.return_date.setMinimumDate(QDate(tanggal_pinjam.year, tanggal_pinjam.month, tanggal_pinjam.day).addDays(1))
        self.return_date.setMaximumDate(QDate(tanggal_pinjam.year, tanggal_pinjam.month, tanggal_pinjam.day).addDays(self.MAX_DAYS))
        self.return_date.setDate(QDate(tanggal_kembali.year, tanggal_kembali.month, tanggal_kembali.day))
        root.addWidget(self.return_date)

        self.mode_info = QLabel()
        self.mode_info.setWordWrap(True)
        root.addWidget(self.mode_info)

        reminder = QLabel("Durasi maksimal 30 hari. Kembalikan buku sebelum jatuh tempo agar tidak tercatat terlambat.")
        reminder.setObjectName("detail_hint")
        reminder.setWordWrap(True)
        root.addWidget(reminder)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Cancel).setText("Batal")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        self.return_date.dateChanged.connect(self._update_mode)
        self._update_mode()

    def selected_return_date(self) -> date:
        return self.return_date.date().toPython()

    def duration_days(self) -> int:
        return (self.selected_return_date() - self.tanggal_pinjam).days

    def requires_admin_approval(self) -> bool:
        return self.duration_days() > self.DIRECT_DAYS

    def _update_mode(self, *_):
        duration = self.duration_days()
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        if duration <= self.DIRECT_DAYS:
            self.mode_info.setText(f"Durasi {duration} hari • dapat langsung dipinjam")
            self.mode_info.setStyleSheet("color: #166534; font-weight: 750;")
            ok_button.setText("Pinjam Sekarang")
        else:
            self.mode_info.setText(f"Durasi {duration} hari • memerlukan persetujuan admin")
            self.mode_info.setStyleSheet("color: #92400E; font-weight: 750;")
            ok_button.setText("Ajukan Peminjaman")


def _confirm_and_borrow(parent, db, user: dict, book: dict) -> bool:
    """Cek stok, pilih durasi, lalu pinjam langsung atau kirim pengajuan."""
    book = _row_to_dict(book)
    book_id = book.get("id_buku") or book.get("id")

    # Cek stok sebelum dialog agar konfirmasi tidak tampil untuk buku yang habis.
    if hasattr(db, "get_book_by_id") and book_id:
        latest = db.get_book_by_id(book_id)
        if latest is None:
            QMessageBox.warning(parent, "Buku Tidak Ditemukan", "Data buku ini sudah tidak tersedia di katalog.")
            return False
        book = _row_to_dict(latest)

    if int(book.get("stok") or 0) <= 0:
        QMessageBox.information(
            parent,
            "Buku Tidak Tersedia",
            "Buku ini sedang tidak dapat dipinjam karena tidak ada salinan yang tersedia."
        )
        return False

    tanggal_pinjam = date.today()
    dialog = BorrowConfirmationDialog(
        book, tanggal_pinjam, tanggal_pinjam + timedelta(days=7), parent
    )
    if dialog.exec() != QDialog.Accepted:
        return False

    tanggal_kembali = dialog.selected_return_date()
    needs_approval = dialog.requires_admin_approval()

    # Periksa ulang stok setelah dialog ditutup untuk mencegah data tampilan yang sudah berubah.
    latest = db.get_book_by_id(book_id) if hasattr(db, "get_book_by_id") else book
    if latest is None or int(_row_to_dict(latest).get("stok") or 0) <= 0:
        QMessageBox.information(
            parent,
            "Buku Tidak Tersedia",
            "Buku ini baru saja dipinjam atau diajukan oleh anggota lain dan saat ini tidak tersedia."
        )
        return False

    try:
        if needs_approval:
            db.add_pengajuan_peminjaman(
                _member_id(user), book_id,
                tanggal_pinjam.isoformat(), tanggal_kembali.isoformat()
            )
            QMessageBox.information(
                parent,
                "Pengajuan Terkirim",
                f"Pengajuan peminjaman '{book.get('judul', '-')}' telah dikirim.\n\n"
                f"Durasi lebih dari 7 hari sehingga perlu persetujuan admin.\n"
                f"Batas pengembalian yang diajukan: {tanggal_kembali.isoformat()}"
            )
        else:
            db.add_peminjaman(
                _member_id(user), book_id,
                tanggal_pinjam.isoformat(), tanggal_kembali.isoformat()
            )
            QMessageBox.information(
                parent,
                "Peminjaman Berhasil",
                f"Buku '{book.get('judul', '-')}' berhasil dipinjam.\n\n"
                f"Batas pengembalian: {tanggal_kembali.isoformat()}"
            )
        return True
    except Exception as exc:
        message = str(exc)
        if "stok" in message.lower() or "habis" in message.lower():
            QMessageBox.information(
                parent,
                "Buku Tidak Tersedia",
                "Buku ini baru saja dipinjam atau diajukan oleh anggota lain dan saat ini tidak tersedia."
            )
        else:
            QMessageBox.warning(
                parent,
                "Peminjaman Gagal",
                f"Peminjaman tidak dapat diproses.\n\n{message}"
            )
        return False


class BookDetailDialog(QDialog):
    """Dialog detail buku dengan aksi pinjam opsional."""

    def __init__(self, book: dict, parent=None, on_borrow=None):
        super().__init__(parent)
        self.book = _row_to_dict(book)
        self.on_borrow = on_borrow
        self.setWindowTitle("Detail Buku")
        self.setObjectName("clean_dialog")
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("detail_header")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(4)
        header_title = QLabel("Detail Buku")
        header_title.setObjectName("detail_dialog_title")
        header_layout.addWidget(header_title)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setSpacing(18)
        body.addWidget(_cover_label(self.book.get("image_path", ""), 112, 154), 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(10)

        title = QLabel(str(self.book.get("judul", "-")))
        title.setObjectName("detail_book_title")
        title.setWordWrap(True)
        info.addWidget(title)

        meta = QLabel(f"{self.book.get('kategori', '-')} • {self.book.get('tahun_terbit', '-')}")
        meta.setObjectName("book_meta")
        meta.setWordWrap(True)
        info.addWidget(meta)

        desc_box = QFrame()
        desc_box.setObjectName("detail_description_box")
        desc_layout = QVBoxLayout(desc_box)
        desc_layout.setContentsMargins(12, 10, 12, 10)
        desc_layout.setSpacing(4)
        desc_title = QLabel("Deskripsi")
        desc_title.setObjectName("detail_description_title")
        desc_text_value = str(self.book.get("deskripsi") or "").strip()
        if not desc_text_value:
            desc_text_value = "Deskripsi buku belum ditambahkan admin."
        desc_text = QLabel(desc_text_value)
        desc_text.setObjectName("detail_description_text")
        desc_text.setWordWrap(True)
        desc_layout.addWidget(desc_title)
        desc_layout.addWidget(desc_text)
        info.addWidget(desc_box)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        stok = int(self.book.get("stok") or 0)
        total_stok = int(self.book.get("total_stok") or stok)
        detail_rows = [
            ("Penulis", self.book.get("penulis", "-")),
            ("Penerbit", self.book.get("penerbit", "-")),
            ("Stok Tersedia", f"{stok} buku"),
            ("Total Koleksi", f"{total_stok} buku"),
        ]
        for index, (key, value) in enumerate(detail_rows):
            cell = QFrame()
            cell.setObjectName("detail_info_cell")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(10, 8, 10, 8)
            cell_layout.setSpacing(2)
            key_label = QLabel(key)
            key_label.setObjectName("detail_info_label")
            value_label = QLabel(str(value))
            value_label.setObjectName("detail_info_value")
            value_label.setWordWrap(True)
            cell_layout.addWidget(key_label)
            cell_layout.addWidget(value_label)
            grid.addWidget(cell, index // 2, index % 2)
        info.addLayout(grid)

        if stok > 0:
            availability_text = "Bisa dipinjam"
            availability_name = "detail_available"
        else:
            availability_text = "Tidak tersedia"
            availability_name = "detail_unavailable"
        availability = QLabel(availability_text)
        availability.setObjectName(availability_name)
        availability.setWordWrap(True)
        info.addWidget(availability)

        body.addLayout(info, 1)
        root.addLayout(body)

        button_row = QHBoxLayout()
        button_row.addStretch()
        close_btn = QPushButton("Tutup")
        close_btn.setObjectName("btn_member_outline")
        close_btn.clicked.connect(self.reject)
        button_row.addWidget(close_btn)

        if self.on_borrow is not None:
            borrow_btn = QPushButton("Pinjam Buku")
            borrow_btn.setObjectName("btn_member_primary")
            borrow_btn.clicked.connect(self._borrow)
            button_row.addWidget(borrow_btn)

        root.addLayout(button_row)

    def _borrow(self):
        if self.on_borrow is not None and self.on_borrow(self.book):
            self.accept()


class MemberHomeWidget(QWidget):
    def __init__(self, db, user: dict, go_to_callback=None):
        super().__init__()
        self.db = db
        self.user = _row_to_dict(user)
        self.go_to = go_to_callback
        self.setObjectName("page")

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 24, 24, 24)
        self.root.setSpacing(16)
        self._build_ui()

    def _build_ui(self):
        hero = QFrame()
        hero.setObjectName("member_hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(16)

        text = QVBoxLayout()
        text.setSpacing(8)
        self.welcome_label = QLabel(f"Selamat Datang, {self.user.get('nama_lengkap', 'Anggota')}")
        self.welcome_label.setObjectName("member_hero_title")
        self.welcome_label.setStyleSheet("color: #FFFFFF; font-size: 24px; font-weight: 900; background: transparent;")
        tagline = QLabel("Baca yang perlu, pinjam yang tepat — PustakaDesk bantu menjaga alurnya tetap rapi.")
        tagline.setObjectName("member_hero_subtitle")
        tagline.setStyleSheet("color: #E0ECFF; font-size: 13px; background: transparent;")
        tagline.setWordWrap(True)
        text.addWidget(self.welcome_label)
        text.addWidget(tagline)

        catalog_btn = QPushButton("Cari Buku")
        catalog_btn.setObjectName("btn_member_primary")
        loans_btn = QPushButton("Pinjaman Saya")
        loans_btn.setObjectName("btn_member_outline")
        if self.go_to:
            catalog_btn.clicked.connect(lambda: self.go_to("Cari Buku"))
            loans_btn.clicked.connect(lambda: self.go_to("Pinjaman Saya"))

        actions = QVBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(catalog_btn)
        actions.addWidget(loans_btn)

        hero_layout.addLayout(text, 1)
        hero_layout.addLayout(actions)
        self.root.addWidget(hero)

        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(12)
        self.root.addLayout(self.stats_layout)

        self.feed_scroll = QScrollArea()
        self.feed_scroll.setObjectName("member_scroll")
        self.feed_scroll.setFrameShape(QFrame.NoFrame)
        self.feed_scroll.setWidgetResizable(True)
        self.feed_container = QWidget()
        self.feed_container.setObjectName("member_scroll_content")
        feed = QVBoxLayout(self.feed_container)
        feed.setContentsMargins(0, 0, 0, 0)
        feed.setSpacing(14)

        rec_title = QLabel("Rekomendasi Buku")
        rec_title.setObjectName("member_section_title")
        feed.addWidget(rec_title)
        self.recommend_layout = QVBoxLayout()
        self.recommend_layout.setSpacing(10)
        feed.addLayout(self.recommend_layout)

        latest_title = QLabel("Buku Terbaru")
        latest_title.setObjectName("member_section_title")
        feed.addWidget(latest_title)
        self.books_layout = QVBoxLayout()
        self.books_layout.setSpacing(10)
        feed.addLayout(self.books_layout)
        feed.addStretch()

        self.feed_scroll.setWidget(self.feed_container)
        self.root.addWidget(self.feed_scroll, 1)
        self.refresh()

    def _stat_card(self, label, value, note):
        card = QFrame()
        card.setObjectName("member_stat_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        title = QLabel(label)
        title.setObjectName("member_stat_title")
        val = QLabel(str(value))
        val.setObjectName("member_stat_value")
        desc = QLabel(note)
        desc.setObjectName("member_stat_note")
        layout.addWidget(title)
        layout.addWidget(val)
        layout.addWidget(desc)
        return card

    def refresh(self):
        if hasattr(self, "welcome_label"):
            self.welcome_label.setText(f"Selamat Datang, {self.user.get('nama_lengkap', 'Anggota')}")
        _clear_layout(self.stats_layout)
        _clear_layout(self.recommend_layout)
        _clear_layout(self.books_layout)

        stats = {"dipinjam": 0, "terlambat": 0, "riwayat": 0, "tersedia": 0}
        if hasattr(self.db, "get_member_stats"):
            stats.update(self.db.get_member_stats(_member_id(self.user)))

        cards = [
            ("Pinjaman Aktif", stats.get("dipinjam", 0), "Belum selesai"),
            ("Terlambat", stats.get("terlambat", 0), "Perlu dicek"),
            ("Riwayat", stats.get("riwayat", 0), "Transaksi selesai"),
            ("Buku Tersedia", stats.get("tersedia", 0), "Siap dipinjam"),
        ]
        for label, value, note in cards:
            self.stats_layout.addWidget(self._stat_card(label, value, note))

        recommendations = []
        if hasattr(self.db, "get_recommended_books"):
            recommendations = [_row_to_dict(book) for book in self.db.get_recommended_books(limit=4)]
        for book in recommendations:
            count = int(book.get("total_pinjam") or 0)
            note = f"Pilihan kategori {book.get('kategori', 'Umum')}"
            if count > 0:
                note += f" • {count}x dipinjam"
            self.recommend_layout.addWidget(self._book_row(book, note=note))
        if not recommendations:
            empty = QLabel("Rekomendasi akan muncul setelah katalog tersedia.")
            empty.setObjectName("member_empty")
            empty.setAlignment(Qt.AlignCenter)
            self.recommend_layout.addWidget(empty)

        books = []
        if hasattr(self.db, "get_all_books"):
            books = [_row_to_dict(book) for book in self.db.get_all_books(sort_col="tahun_terbit", sort_order="DESC")][:4]
        for book in books:
            self.books_layout.addWidget(self._book_row(book))
        if not books:
            empty = QLabel("Belum ada buku yang tersedia di katalog.")
            empty.setObjectName("member_empty")
            empty.setAlignment(Qt.AlignCenter)
            self.books_layout.addWidget(empty)

    def _book_row(self, book, note: str = ""):
        card = ClickableBookCard()
        card.setObjectName("book_card")
        card.setMinimumHeight(94)
        card.setToolTip("Klik untuk melihat detail buku")
        card.clicked.connect(lambda b=book: self.show_detail(b))
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        cover = _cover_label(book.get("image_path", ""), 48, 66)
        cover.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(cover)

        text = QVBoxLayout()
        text.setSpacing(4)
        title = QLabel(book.get("judul", "-"))
        title.setObjectName("book_title")
        title.setWordWrap(True)
        author = QLabel(f"{book.get('penulis', '-')} • {book.get('kategori', '-')}")
        author.setObjectName("book_author")
        author.setWordWrap(True)
        if note:
            meta_text = note
            meta_name = "book_note"
        elif int(book.get("stok") or 0) > 0:
            meta_text = "Bisa dipinjam"
            meta_name = "book_available"
        else:
            meta_text = "Tidak tersedia"
            meta_name = "book_unavailable"
        meta = QLabel(meta_text)
        meta.setObjectName(meta_name)
        meta.setWordWrap(True)
        for label in (title, author, meta):
            label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text.addWidget(title)
        text.addWidget(author)
        text.addWidget(meta)
        layout.addLayout(text, 1)

        action = QLabel("Lihat detail  ›")
        action.setObjectName("book_row_action")
        action.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        action.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(action)
        return card

    def show_detail(self, book):
        BookDetailDialog(book, self, on_borrow=self.borrow_book).exec()

    def borrow_book(self, book):
        if _confirm_and_borrow(self, self.db, self.user, book):
            self.refresh()
            return True
        return False


class MemberCatalogWidget(QWidget):
    def __init__(self, db, user: dict):
        super().__init__()
        self.db = db
        self.user = _row_to_dict(user)
        self.setObjectName("page")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        root.addWidget(_section_header("Cari Buku"))

        toolbar = QFrame()
        toolbar.setObjectName("member_toolbar")
        top_bar = QHBoxLayout(toolbar)
        top_bar.setContentsMargins(14, 12, 14, 12)
        top_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari judul atau penulis...")
        self.category_filter = QComboBox()
        self.category_filter.addItem("Semua Kategori")
        if hasattr(self.db, "get_kategori_list"):
            for kategori in self.db.get_kategori_list():
                self.category_filter.addItem(kategori)

        top_bar.addWidget(QLabel("Cari"))
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(QLabel("Kategori"))
        top_bar.addWidget(self.category_filter)
        root.addWidget(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("member_scroll")
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setObjectName("member_scroll_content")
        self.books_layout = QGridLayout(self.container)
        self.books_layout.setSpacing(14)
        self.books_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

        self.search_input.textChanged.connect(self.load_books)
        self.category_filter.currentTextChanged.connect(self.load_books)
        self.load_books()

    def load_books(self):
        _clear_layout(self.books_layout)

        books = []
        if hasattr(self.db, "get_all_books"):
            books = [_row_to_dict(book) for book in self.db.get_all_books()]

        keyword = self.search_input.text().lower().strip()
        kategori = self.category_filter.currentText()
        filtered = []

        for book in books:
            judul = str(book.get("judul", "")).lower()
            penulis = str(book.get("penulis", "")).lower()
            kategori_buku = str(book.get("kategori", ""))
            cocok_search = keyword in judul or keyword in penulis
            cocok_kategori = kategori == "Semua Kategori" or kategori == kategori_buku
            if cocok_search and cocok_kategori:
                filtered.append(book)

        if not filtered:
            empty = QLabel("Buku tidak ditemukan. Coba ubah kata kunci atau kategori.")
            empty.setObjectName("member_empty")
            empty.setAlignment(Qt.AlignCenter)
            self.books_layout.addWidget(empty, 0, 0)
            return

        row = col = 0
        for book in filtered:
            self.books_layout.addWidget(self._book_card(book), row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _book_card(self, book):
        card = QFrame()
        card.setObjectName("book_card")
        card.setMinimumHeight(250)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        cover_row = QHBoxLayout()
        cover_row.addStretch()
        cover_row.addWidget(_cover_label(book.get("image_path", "")))
        cover_row.addStretch()

        title = QLabel(book.get("judul", "-"))
        title.setObjectName("book_title")
        title.setWordWrap(True)
        author = QLabel(book.get("penulis", "-"))
        author.setObjectName("book_author")
        author.setWordWrap(True)
        category = QLabel(f"{book.get('kategori', '-')} • {book.get('tahun_terbit', '-')}")
        category.setObjectName("book_meta")
        is_available = int(book.get("stok") or 0) > 0
        stock = QLabel("Bisa dipinjam" if is_available else "Tidak tersedia")
        stock.setObjectName("book_available" if is_available else "book_unavailable")

        button_layout = QHBoxLayout()
        detail_btn = QPushButton("Detail")
        detail_btn.setObjectName("btn_member_outline")
        borrow_btn = QPushButton("Pinjam")
        borrow_btn.setObjectName("btn_member_primary")

        detail_btn.clicked.connect(lambda _, b=book: self.show_detail(b))
        borrow_btn.clicked.connect(lambda _, b=book: self.borrow_book(b))
        button_layout.addWidget(detail_btn)
        button_layout.addWidget(borrow_btn)

        layout.addLayout(cover_row)
        layout.addWidget(title)
        layout.addWidget(author)
        layout.addWidget(category)
        layout.addWidget(stock)
        layout.addStretch()
        layout.addLayout(button_layout)
        return card

    def show_detail(self, book):
        BookDetailDialog(book, self, on_borrow=self.borrow_book).exec()

    def borrow_book(self, book):
        if _confirm_and_borrow(self, self.db, self.user, book):
            self.load_books()
            return True
        return False

    def refresh(self):
        self.load_books()


class MemberLoansWidget(QWidget):
    def __init__(self, db, user: dict, history: bool = False):
        super().__init__()
        self.db = db
        self.user = _row_to_dict(user)
        self.history = history
        self.setObjectName("page")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        root.addWidget(_section_header("Riwayat Peminjaman" if self.history else "Pinjaman Saya"))

        toolbar = QFrame()
        toolbar.setObjectName("member_toolbar")
        top_bar = QHBoxLayout(toolbar)
        top_bar.setContentsMargins(14, 12, 14, 12)
        top_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari judul buku...")
        self.filter_status = QComboBox()
        if self.history:
            self.filter_status.addItems(["Dikembalikan"])
        else:
            self.filter_status.addItems(["Semua", "Menunggu Persetujuan", "Dipinjam", "Konfirmasi", "Terlambat", "Ditolak"])

        search_btn = QPushButton("Cari")
        search_btn.setObjectName("btn_member_primary")
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("btn_member_outline")
        search_btn.clicked.connect(self.load_loans)
        refresh_btn.clicked.connect(self.refresh)
        self.filter_status.currentTextChanged.connect(self.load_loans)
        self.search_input.textChanged.connect(self.load_loans)

        top_bar.addWidget(QLabel("Cari"))
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(QLabel("Status"))
        top_bar.addWidget(self.filter_status)
        top_bar.addWidget(search_btn)
        top_bar.addWidget(refresh_btn)
        root.addWidget(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("member_scroll")
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setObjectName("member_scroll_content")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setSpacing(12)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)
        self.load_loans()

    def load_loans(self):
        _clear_layout(self.list_layout)

        keyword = self.search_input.text().strip()
        status_filter = self.filter_status.currentText()
        status = "Riwayat" if self.history else "Pinjaman Saya"

        loans = self.db.get_user_peminjaman(_member_id(self.user), keyword, status)
        loans = [_row_to_dict(loan) for loan in loans]

        shown = 0
        for loan in loans:
            judul = str(loan.get("judul", "")).lower()
            loan_status = loan.get("status", "-")
            cocok_search = keyword.lower() in judul
            cocok_status = ((status_filter == "Semua" and loan_status != "Ditolak") or loan_status == status_filter)
            if cocok_search and cocok_status:
                self.list_layout.addWidget(self._loan_card(loan))
                shown += 1

        if shown == 0:
            empty = QLabel("Belum ada data peminjaman yang sesuai.")
            empty.setObjectName("member_empty")
            empty.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty)

        self.list_layout.addStretch()

    def _status_object_name(self, status):
        if status == "Terlambat":
            return "loan_status_late"
        if status == "Konfirmasi":
            return "loan_status_confirm"
        if status == "Menunggu Persetujuan":
            return "loan_status_pending"
        if status == "Ditolak":
            return "loan_status_rejected"
        return "loan_status"

    def _loan_card(self, loan):
        card = QFrame()
        card.setObjectName("loan_card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Gunakan rasio sampul buku, bukan kotak, supaya gambar asli tidak terpotong
        # dan tetap terlihat natural pada daftar pinjaman.
        cover = _cover_label(loan.get("image_path", ""), 64, 92)
        layout.addWidget(cover, 0, Qt.AlignVCenter)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(3)

        title = QLabel(loan.get("judul", "-"))
        title.setObjectName("loan_title")
        title.setWordWrap(True)
        content.addWidget(title)

        info_row = QHBoxLayout()
        info_row.setContentsMargins(0, 1, 0, 0)
        info_row.setSpacing(18)
        info_row.addWidget(
            _loan_info_item(
                "Tanggal pinjam",
                _format_member_date(loan.get("tanggal_pinjam")),
            )
        )
        info_row.addWidget(
            _loan_info_item(
                "Jatuh tempo",
                _format_member_date(loan.get("tanggal_kembali")),
            )
        )

        actual_return = loan.get("tanggal_kembali_aktual")
        loan_status = loan.get("status")
        if actual_return:
            actual_label = "Dikembalikan" if loan_status == "Dikembalikan" else "Pengajuan kembali"
            info_row.addWidget(
                _loan_info_item(actual_label, _format_member_date(actual_return))
            )

        try:
            fine = int(float(loan.get("denda") or 0))
        except (TypeError, ValueError):
            fine = 0
        if fine > 0:
            info_row.addWidget(
                _loan_info_item("Denda", _format_rupiah(fine), "loan_info_value_late")
            )

        info_row.addStretch()
        content.addLayout(info_row)

        if loan_status == "Menunggu Persetujuan":
            note = QLabel("Durasi lebih dari 7 hari · menunggu keputusan admin")
            note.setObjectName("loan_note")
            content.addWidget(note)
        elif loan_status == "Ditolak":
            note = QLabel("Pengajuan peminjaman tidak disetujui admin")
            note.setObjectName("loan_note_rejected")
            content.addWidget(note)

        status_box = QVBoxLayout()
        status_box.setSpacing(8)
        status_box.setAlignment(Qt.AlignTop)
        status_label = QLabel(str(loan_status or "-"))
        status_label.setObjectName(self._status_object_name(loan_status))
        status_label.setAlignment(Qt.AlignCenter)
        status_box.addWidget(status_label)

        if not self.history:
            if loan_status in ("Dipinjam", "Terlambat"):
                return_btn = QPushButton("Ajukan Pengembalian")
                return_btn.setObjectName("btn_member_primary")
                return_btn.clicked.connect(lambda _, item=loan: self.request_return(item))
                status_box.addWidget(return_btn)
            elif loan_status in ("Konfirmasi", "Menunggu Persetujuan"):
                waiting = QPushButton("Menunggu Admin")
                waiting.setObjectName("btn_member_outline")
                waiting.setEnabled(False)
                status_box.addWidget(waiting)
            elif loan_status == "Ditolak":
                rejected = QPushButton("Pengajuan Ditolak")
                rejected.setObjectName("btn_member_outline")
                rejected.setEnabled(False)
                status_box.addWidget(rejected)

        layout.addLayout(content, 1)
        layout.addLayout(status_box)
        return card

    def request_return(self, loan):
        confirm = QMessageBox.question(
            self,
            "Ajukan Pengembalian",
            "Ajukan pengembalian buku ini?\n\nStatus akan menjadi Konfirmasi sampai admin menerima buku fisik.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            denda = self.db.ajukan_pengembalian(
                loan.get("id_peminjaman"),
                date.today().isoformat()
            )
            QMessageBox.information(
                self,
                "Pengembalian Diajukan",
                f"Pengembalian berhasil diajukan.\nMenunggu konfirmasi admin.\nEstimasi denda: Rp {int(denda):,}".replace(",", ".")
            )
            self.load_loans()
        except Exception as e:
            QMessageBox.warning(self, "Gagal", f"Pengajuan pengembalian gagal.\n\n{e}")

    def refresh(self):
        self.load_loans()


class MemberProfileWidget(QWidget):
    def __init__(self, db, user: dict, on_user_updated=None):
        super().__init__()
        self.db = db
        self.user = _row_to_dict(user)
        self.on_user_updated = on_user_updated
        self.pending_profile_image_path = None
        self.setObjectName("page")

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 24, 24, 24)
        self.root.setSpacing(16)
        self.root.addWidget(_section_header("Profil Akun"))

        content = QHBoxLayout()
        content.setSpacing(16)
        self.root.addLayout(content, 1)

        self.summary_card = QFrame()
        self.summary_card.setObjectName("profile_card")
        summary = QVBoxLayout(self.summary_card)
        summary.setContentsMargins(18, 18, 18, 18)
        summary.setSpacing(12)

        self.avatar = QLabel()
        self.avatar.setObjectName("profile_picture")
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFixedSize(96, 96)

        photo_actions = QHBoxLayout()
        self.btn_photo = QPushButton("Ubah Foto")
        self.btn_photo.setObjectName("btn_member_outline")
        self.btn_remove_photo = QPushButton("Hapus Foto")
        self.btn_remove_photo.setObjectName("btn_member_outline")
        self.btn_photo.clicked.connect(self.choose_profile_picture)
        self.btn_remove_photo.clicked.connect(self.remove_profile_picture)
        photo_actions.addWidget(self.btn_photo)
        photo_actions.addWidget(self.btn_remove_photo)

        self.name_label = QLabel()
        self.name_label.setObjectName("profile_name")
        self.name_label.setWordWrap(True)

        summary.addWidget(self.avatar, 0, Qt.AlignLeft)
        summary.addLayout(photo_actions)
        summary.addWidget(self.name_label)

        note = QLabel("Foto profil hanya digunakan untuk memperjelas identitas akun di tampilan anggota.")
        note.setObjectName("profile_note")
        note.setWordWrap(True)
        summary.addWidget(note)
        summary.addStretch()

        self.form_card = QFrame()
        self.form_card.setObjectName("profile_card")
        form_box = QVBoxLayout(self.form_card)
        form_box.setContentsMargins(18, 18, 18, 18)
        form_box.setSpacing(12)

        form_title = QLabel("Edit Data Anggota")
        form_title.setObjectName("profile_form_title")
        form_hint = QLabel("Kosongkan password jika tidak ingin mengganti.")
        form_hint.setObjectName("profile_meta")
        form_hint.setWordWrap(True)
        form_box.addWidget(form_title)
        form_box.addWidget(form_hint)

        form = QFormLayout()
        form.setContentsMargins(0, 6, 0, 0)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)

        self.input_nama = QLineEdit()
        self.input_nama.setPlaceholderText("Nama lengkap")
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Username")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Password baru (opsional)")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_confirm = QLineEdit()
        self.input_confirm.setPlaceholderText("Ulangi password baru")
        self.input_confirm.setEchoMode(QLineEdit.Password)

        form.addRow("Nama Lengkap", self.input_nama)
        form.addRow("Username", self.input_username)
        form.addRow("Password Baru", self.input_password)
        form.addRow("Konfirmasi", self.input_confirm)
        form_box.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch()
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setObjectName("btn_member_outline")
        self.btn_save = QPushButton("Simpan Perubahan")
        self.btn_save.setObjectName("btn_member_primary")
        self.btn_reset.clicked.connect(self.reset_form)
        self.btn_save.clicked.connect(self.save_profile)
        actions.addWidget(self.btn_reset)
        actions.addWidget(self.btn_save)
        form_box.addLayout(actions)

        content.addWidget(self.summary_card, 1)
        content.addWidget(self.form_card, 2)

        stats_title = QLabel("Ringkasan Aktivitas")
        stats_title.setObjectName("member_section_title")
        self.root.addWidget(stats_title)

        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(12)
        self.root.addLayout(self.stats_layout)
        self.refresh()

    def _initials(self):
        name = str(self.user.get("nama_lengkap") or self.user.get("username") or "A")
        parts = [p for p in name.replace("_", " ").split() if p]
        if not parts:
            return "A"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][:1] + parts[-1][:1]).upper()

    def _small_stat(self, label, value, note):
        card = QFrame()
        card.setObjectName("member_stat_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        title = QLabel(label)
        title.setObjectName("member_stat_title")
        val = QLabel(str(value))
        val.setObjectName("member_stat_value")
        desc = QLabel(note)
        desc.setObjectName("member_stat_note")
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(val)
        layout.addWidget(desc)
        return card

    def _load_current_user(self):
        user_id = _member_id(self.user)
        if user_id and hasattr(self.db, "get_user_by_id"):
            current = self.db.get_user_by_id(user_id)
            if current:
                self.user = _row_to_dict(current)

    def _render_avatar(self):
        image_path = self.user.get("profile_image_path", "")
        if self.pending_profile_image_path is not None:
            image_path = self.pending_profile_image_path
        _apply_profile_picture(self.avatar, image_path, self._initials(), 96)

    def choose_profile_picture(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Foto Profil",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not filepath:
            return
        try:
            self.pending_profile_image_path = _copy_profile_image(filepath)
            self._render_avatar()
        except Exception as e:
            QMessageBox.warning(self, "Gagal", f"Foto profil gagal dipilih.\n\n{e}")

    def remove_profile_picture(self):
        self.pending_profile_image_path = ""
        self._render_avatar()

    def reset_form(self):
        self.pending_profile_image_path = None
        self.input_nama.setText(str(self.user.get("nama_lengkap", "")))
        self.input_username.setText(str(self.user.get("username", "")))
        self.input_password.clear()
        self.input_confirm.clear()
        self._render_avatar()

    def refresh(self):
        self._load_current_user()
        self.pending_profile_image_path = None
        self.name_label.setText(str(self.user.get("nama_lengkap", "-")))
        self.reset_form()

        _clear_layout(self.stats_layout)
        stats = {"dipinjam": 0, "terlambat": 0, "riwayat": 0, "tersedia": 0}
        if hasattr(self.db, "get_member_stats"):
            stats.update(self.db.get_member_stats(_member_id(self.user)))

        cards = [
            ("Pinjaman Aktif", stats.get("dipinjam", 0), "Belum selesai"),
            ("Terlambat", stats.get("terlambat", 0), "Lewat tempo"),
            ("Total Riwayat", stats.get("riwayat", 0), "Transaksi selesai"),
            ("Katalog Tersedia", stats.get("tersedia", 0), "Bisa dipinjam"),
        ]
        for label, value, note in cards:
            self.stats_layout.addWidget(self._small_stat(label, value, note))

    def save_profile(self):
        user_id = _member_id(self.user)
        nama = self.input_nama.text().strip()
        username = self.input_username.text().strip()
        password = self.input_password.text()
        confirm = self.input_confirm.text()

        if not user_id:
            QMessageBox.warning(self, "Gagal", "Akun tidak ditemukan.")
            return
        if not nama or not username:
            QMessageBox.warning(self, "Data Belum Lengkap", "Nama lengkap dan username wajib diisi.")
            return
        if password or confirm:
            if password != confirm:
                QMessageBox.warning(self, "Password Tidak Sama", "Password baru dan konfirmasi harus sama.")
                return
            if len(password) < 4:
                QMessageBox.warning(self, "Password Terlalu Pendek", "Password minimal 4 karakter.")
                return

        try:
            self.db.update_user(
                user_id,
                username,
                nama,
                self.user.get("role", "anggota"),
                password,
                self.pending_profile_image_path
            )
            self._load_current_user()
            self.pending_profile_image_path = None
            self.reset_form()
            self.name_label.setText(str(self.user.get("nama_lengkap", "-")))
            self.username_label.setText(f"Username: {self.user.get('username', '-')}")
            if self.on_user_updated:
                self.on_user_updated(dict(self.user))
            QMessageBox.information(self, "Berhasil", "Profil berhasil diperbarui.")
        except Exception as e:
            msg = str(e)
            if "UNIQUE" in msg.upper() and "USERNAME" in msg.upper():
                msg = "Username sudah digunakan akun lain. Gunakan username berbeda."
            QMessageBox.warning(self, "Gagal", f"Profil gagal diperbarui.\n\n{msg}")
