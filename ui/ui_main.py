"""
PustakaDesk — ui_main.py

Admin memakai halaman dashboard, buku, user, peminjaman, dan laporan.
Anggota memakai halaman dari ui_member.py.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from ui.ui_dashboard import DashboardWidget
from ui.ui_buku import BukuWidget
from ui.ui_user import UserWidget
from ui.ui_peminjaman import PeminjamanWidget
from ui.ui_laporan import LaporanWidget

from ui.ui_member import (
    MemberHomeWidget,
    MemberCatalogWidget,
    MemberLoansWidget,
    MemberProfileWidget
)

def _nav_btn(icon, label):
    btn = QPushButton(f"{icon}   {label}")
    btn.setObjectName("nav_button")
    btn.setCheckable(True)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(42)
    return btn


class MainWindow(QMainWindow):
    def __init__(self, db, user: dict, app, load_stylesheet_fn, dark=False):
        super().__init__()
        self.db = db
        self.user = dict(user)
        self.app = app
        self.load_stylesheet = load_stylesheet_fn
        self._dark = dark
        self.role = str(self.user.get("role", "anggota")).lower().strip()
        self.is_admin = self.role == "admin"

        title_role = "Admin" if self.is_admin else "Anggota"
        self.setWindowTitle(f"PustakaDesk — {title_role}")
        self.setMinimumSize(1050, 650)
        self.resize(1180, 700)

        self._build_ui()
        self._build_menu()
        self._build_statusbar()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("main_root")
        self.setCentralWidget(central)

        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)

        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(14, 16, 14, 14)
        sb.setSpacing(10)

        brand = QFrame()
        brand.setObjectName("sidebar_brand")
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(12, 12, 12, 12)
        brand_layout.setSpacing(10)

        logo = QLabel("📚")
        logo.setObjectName("brand_icon")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(40, 40)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)

        lbl_app = QLabel("PustakaDesk")
        lbl_app.setObjectName("sidebar_app_name")

        lbl_sub = QLabel("Admin Panel" if self.is_admin else "Library Portal")
        lbl_sub.setObjectName("sidebar_app_sub")

        brand_text.addWidget(lbl_app)
        brand_text.addWidget(lbl_sub)

        brand_layout.addWidget(logo)
        brand_layout.addLayout(brand_text)
        sb.addWidget(brand)

        user_card = QFrame()
        user_card.setObjectName("sidebar_user_card")

        uc = QVBoxLayout(user_card)
        uc.setContentsMargins(12, 10, 12, 10)
        uc.setSpacing(2)

        lbl_role = QLabel("ADMIN" if self.is_admin else "ANGGOTA")
        lbl_role.setObjectName("sidebar_user_role")

        self.lbl_name = QLabel(
            self.user.get("nama_lengkap")
            or self.user.get("username")
            or ("Admin" if self.is_admin else "Anggota")
        )
        self.lbl_name.setObjectName("sidebar_user_name")

        uc.addWidget(lbl_role)
        uc.addWidget(self.lbl_name)
        sb.addWidget(user_card)

        section = QLabel("MENU ADMIN" if self.is_admin else "MENU ANGGOTA")
        section.setObjectName("sidebar_section_label")
        sb.addWidget(section)

        self._stack = QStackedWidget()
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        self._nav_index = {}
        self._nav_label_by_index = {}

        for i, (icon, label) in enumerate(self._nav_items()):
            btn = _nav_btn(icon, label)
            self._btn_group.addButton(btn, i)
            sb.addWidget(btn)

            self._nav_index[label] = i
            self._nav_label_by_index[i] = label
            self._stack.addWidget(self._make_page(label))

        self._btn_group.buttons()[0].setChecked(True)
        # Jangan langsung mengubah index stack. Semua perpindahan halaman harus
        # melalui _go_to() agar data halaman tujuan dimuat ulang dari database.
        self._btn_group.idClicked.connect(self._on_nav_clicked)

        sb.addStretch()

        logout = QPushButton("🚪   Logout")
        logout.setObjectName("btn_logout_sidebar")
        logout.setCursor(Qt.PointingHandCursor)
        logout.setMinimumHeight(42)
        logout.clicked.connect(self._on_logout)
        sb.addWidget(logout)

        h.addWidget(sidebar)
        h.addWidget(self._stack, 1)

    def _nav_items(self):
        if self.is_admin:
            return [
                ("🏠", "Dashboard"),
                ("📚", "Katalog Buku"),
                ("👥", "Manajemen User"),
                ("📋", "Peminjaman"),
                ("📊", "Laporan"),
            ]

        return [
            ("✨", "Beranda"),
            ("🔎", "Cari Buku"),
            ("📖", "Pinjaman Saya"),
            ("🕘", "Riwayat"),
            ("👤", "Profil"),
        ]

    def _make_page(self, label: str) -> QWidget:
        if self.is_admin:
            if label == "Dashboard":
                return DashboardWidget(self.db)

            if label == "Katalog Buku":
                return BukuWidget(self.db)

            if label == "Manajemen User":
                return UserWidget(self.db)

            if label == "Peminjaman":
                return PeminjamanWidget(self.db)

            if label == "Laporan":
                return LaporanWidget(self.db)

        else:
            if label == "Beranda":
                return MemberHomeWidget(self.db, self.user, self._go_to)

            if label == "Cari Buku":
                return MemberCatalogWidget(self.db, self.user)

            if label == "Pinjaman Saya":
                return MemberLoansWidget(self.db, self.user, history=False)

            if label == "Riwayat":
                return MemberLoansWidget(self.db, self.user, history=True)

            if label == "Profil":
                return MemberProfileWidget(self.db, self.user, self._update_logged_user)

        return QWidget()

    def _build_menu(self):
        mb = self.menuBar()

        menu_app = mb.addMenu("Aplikasi")

        act_logout = QAction("Logout dari akun", self)
        act_logout.triggered.connect(self._on_logout)

        act_exit = QAction("Keluar aplikasi", self)
        act_exit.triggered.connect(self.close)

        menu_app.addAction(act_logout)
        menu_app.addSeparator()
        menu_app.addAction(act_exit)

        menu_data = mb.addMenu("Data" if self.is_admin else "Navigasi")
        for label in self._nav_index.keys():
            act = QAction(label, self)
            act.triggered.connect(lambda checked=False, l=label: self._go_to(l))
            menu_data.addAction(act)

        menu_view = mb.addMenu("Tampilan")

        self.act_theme = QAction(
            "Gunakan Tema Terang" if self._dark else "Gunakan Tema Gelap",
            self
        )
        self.act_theme.triggered.connect(self._toggle_theme)
        menu_view.addAction(self.act_theme)

        menu_help = mb.addMenu("Bantuan")

        act_about = QAction("Tentang PustakaDesk", self)
        act_about.triggered.connect(self._show_about)
        menu_help.addAction(act_about)

    def _build_statusbar(self):
        status = self.statusBar()
        status.setObjectName("app_statusbar")
        status.setSizeGripEnabled(False)
        status.setMinimumHeight(28)
        status.show()

        self.lbl_status_members = QLabel(
            "Kelompok 9 |   "
            "Raffi Fatthoni (F1D02310133)  -  "
            "Deswita Salsabila (F1D02410004)  -  "
            "Oktora Rizka Arifin (F1D02410145)"
        )
        self.lbl_status_members.setObjectName("status_members")
        self.lbl_status_members.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        status.addPermanentWidget(self.lbl_status_members, 1)

    def _update_logged_user(self, updated_user: dict):
        """Dipanggil dari halaman profil setelah anggota mengubah data akunnya."""
        if not updated_user:
            return
        self.user.update(dict(updated_user))
        if hasattr(self, "lbl_name"):
            self.lbl_name.setText(
                self.user.get("nama_lengkap")
                or self.user.get("username")
                or ("Admin" if self.is_admin else "Anggota")
            )

        # Bagikan data user terbaru ke halaman anggota lain tanpa mengubah alur fitur.
        for i in range(self._stack.count()):
            widget = self._stack.widget(i)
            if hasattr(widget, "user"):
                widget.user = dict(self.user)

    def _on_nav_clicked(self, index: int):
        """Navigasi sidebar sekaligus menyegarkan halaman yang dibuka."""
        label = self._nav_label_by_index.get(index)
        if label is not None:
            self._go_to(label)

    def _go_to(self, label):
        idx = self._nav_index[label]
        self._stack.setCurrentIndex(idx)
        self._btn_group.button(idx).setChecked(True)

        # View dibuat sekali dan disimpan di QStackedWidget. Karena itu isi view
        # harus dimuat ulang setiap kali dibuka agar perubahan dari view lain
        # (misalnya peminjaman baru) langsung terlihat tanpa login ulang.
        widget = self._stack.widget(idx)
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _toggle_theme(self):
        self._dark = not self._dark
        self.load_stylesheet(self.app, self._dark)

        self.act_theme.setText(
            "Gunakan Tema Terang" if self._dark else "Gunakan Tema Gelap"
        )

    def _on_logout(self):
        confirm = QMessageBox.question(
            self,
            "Logout",
            "Yakin ingin logout dari akun ini?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Logout eksplisit menghapus sesi remember-me lokal. Menutup aplikasi
            # biasa tidak menghapusnya, sehingga akun tetap dapat dipulihkan.
            from utils.session import clear_remembered_user
            clear_remembered_user()

            from ui.ui_login import LoginWindow

            self._login = LoginWindow(
                self.db,
                self.app,
                self.load_stylesheet,
                dark=self._dark,
                try_remembered_session=False,
            )
            self._login.show()
            self.close()

    def _show_about(self):
        QMessageBox.information(
            self,
            "Tentang PustakaDesk",
            "PustakaDesk — Sistem Manajemen Perpustakaan\n\n"
            "Aplikasi desktop PySide6 untuk mengelola katalog buku, anggota, "
            "peminjaman, pengembalian, dan laporan.\n\n"
            "Mode admin menggunakan dashboard operasional, sedangkan anggota "
            "menggunakan tampilan terpisah melalui ui_member.py."
        )