"""
PustakaDesk — ui_dialogs.py
Halaman dialog untuk pinjam dan kembalikan buku
"""

from datetime import date, timedelta

from PySide6.QtWidgets import (
   QDialog, QVBoxLayout, QFormLayout, QComboBox,
   QDateEdit, QLabel, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import QDate


class BorrowDialog(QDialog):
   def __init__(self, db, parent=None):
      super().__init__(parent)

      self.db = db
      self.setWindowTitle("Pinjam Buku")
      self.setMinimumWidth(420)

      layout = QVBoxLayout(self)
      form = QFormLayout()

      self.cb_buku = QComboBox()
      self.cb_user = QComboBox()

      self.books = self.db.get_available_books()
      for book in self.books:
         text = f"{book['judul']} — {book['penulis']} (Stok: {book['stok']})"
         self.cb_buku.addItem(text, book["id_buku"])

      self.users = self.db.get_all_users(role="anggota")
      for user in self.users:
         text = f"{user['nama_lengkap']} ({user['username']})"
         self.cb_user.addItem(text, user["id_user"])

      self.tgl_pinjam = QDateEdit()
      self.tgl_pinjam.setCalendarPopup(True)
      self.tgl_pinjam.setDate(QDate.currentDate())

      self.tgl_kembali = QDateEdit()
      self.tgl_kembali.setCalendarPopup(True)
      self.tgl_kembali.setDate(QDate.currentDate().addDays(7))

      info = QLabel("Denda keterlambatan: Rp 1.000/hari")
      info.setStyleSheet("color: #666;")

      form.addRow("Buku:", self.cb_buku)
      form.addRow("Anggota:", self.cb_user)
      form.addRow("Tanggal Pinjam:", self.tgl_pinjam)
      form.addRow("Tanggal Kembali:", self.tgl_kembali)

      layout.addLayout(form)
      layout.addWidget(info)

      self.button_box = QDialogButtonBox(
         QDialogButtonBox.Save | QDialogButtonBox.Cancel
      )
      self.button_box.accepted.connect(self.save)
      self.button_box.rejected.connect(self.reject)

      layout.addWidget(self.button_box)

   def save(self):
      if self.cb_buku.count() == 0:
         QMessageBox.warning(self, "Gagal", "Tidak ada buku yang tersedia.")
         return

      if self.cb_user.count() == 0:
         QMessageBox.warning(self, "Gagal", "Tidak ada anggota yang tersedia.")
         return

      id_buku = self.cb_buku.currentData()
      id_user = self.cb_user.currentData()

      tanggal_pinjam = self.tgl_pinjam.date().toPython()
      tanggal_kembali = self.tgl_kembali.date().toPython()

      if tanggal_kembali <= tanggal_pinjam:
         QMessageBox.warning(
               self,
               "Tanggal Tidak Valid",
               "Tanggal kembali harus setelah tanggal pinjam."
         )
         return

      try:
         self.db.add_peminjaman(
               id_user,
               id_buku,
               tanggal_pinjam.isoformat(),
               tanggal_kembali.isoformat()
         )

         QMessageBox.information(
               self,
               "Berhasil",
               "Data peminjaman berhasil ditambahkan."
         )

         self.accept()

      except Exception as e:
         QMessageBox.warning(
               self,
               "Gagal",
               f"Peminjaman gagal.\n\n{e}"
         )


class ReturnDialog(QDialog):
   def __init__(self, db, id_peminjaman, tanggal_aktual=None, parent=None):
      super().__init__(parent)

      self.db = db
      self.id_peminjaman = id_peminjaman
      self.tanggal_aktual = tanggal_aktual or date.today().isoformat()

      self.setWindowTitle("Kembalikan Buku")
      self.setMinimumWidth(420)

      layout = QVBoxLayout(self)

      self.data = self.db.get_peminjaman_by_id(id_peminjaman)

      info = QLabel(
         "Konfirmasi pengembalian buku.\n"
         "Denda akan dihitung otomatis jika melewati tanggal kembali."
      )
      info.setWordWrap(True)

      self.tgl_kembali = QDateEdit()
      self.tgl_kembali.setCalendarPopup(True)
      self.tgl_kembali.setDate(QDate.currentDate())

      layout.addWidget(info)

      form = QFormLayout()
      form.addRow("Tanggal Dikembalikan:", self.tgl_kembali)
      layout.addLayout(form)

      self.preview = QLabel("")
      layout.addWidget(self.preview)

      self.tgl_kembali.dateChanged.connect(self.update_preview)
      self.update_preview()

      self.button_box = QDialogButtonBox(
         QDialogButtonBox.Save | QDialogButtonBox.Cancel
      )
      self.button_box.accepted.connect(self.save)
      self.button_box.rejected.connect(self.reject)

      layout.addWidget(self.button_box)

   def update_preview(self):
      if not self.data:
         self.preview.setText("Data peminjaman tidak ditemukan.")
         return

      due = date.fromisoformat(self.data["tanggal_kembali"])
      actual = self.tgl_kembali.date().toPython()

      terlambat = max(0, (actual - due).days)
      denda = terlambat * 1000

      self.preview.setText(
         f"Terlambat: {terlambat} hari\n"
         f"Estimasi denda: Rp {denda:,}".replace(",", ".")
      )

   def save(self):
      try:
         tanggal_aktual = self.tgl_kembali.date().toPython().isoformat()

         denda = self.db.kembalikan_buku(
               self.id_peminjaman,
               tanggal_aktual
         )

         QMessageBox.information(
               self,
               "Berhasil",
               f"Buku berhasil dikembalikan.\nDenda: Rp {int(denda):,}".replace(",", ".")
         )

         self.accept()

      except Exception as e:
         QMessageBox.warning(
               self,
               "Gagal",
               f"Pengembalian gagal.\n\n{e}"
         )