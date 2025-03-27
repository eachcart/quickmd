import sys
import os
import hashlib
import json
from PyQt6 import QtWidgets, QtGui, QtCore
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode

class QuickMD(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuickMD")
        self.resize(600, 400)
        self.mode = None  # check / create / edit
        self.file_hashes = {}

        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.layout = QtWidgets.QVBoxLayout(self.central)

        self.list_widget = QtWidgets.QListWidget()
        self.layout.addWidget(self.list_widget)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.accept_btn = QtWidgets.QPushButton("Accept")
        self.accept_btn.setVisible(False)
        self.accept_btn.clicked.connect(self.save_qmd)
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.button_layout.addWidget(self.accept_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.close_btn)
        self.layout.addLayout(self.button_layout)

        menu = self.menuBar().addMenu("File")
        menu.addAction("Check .qmd", self.check_qmd)
        menu.addSeparator()
        menu.addAction("Create .qmd", self.create_qmd)
        menu.addAction("Edit .qmd", self.edit_qmd)

        edit_menu = self.menuBar().addMenu("Tools")
        edit_menu.addAction("Add file", self.add_file)
        edit_menu.addAction("Remove selected", self.remove_selected)
        edit_menu.addAction("Update md5", self.update_md5)

        self.icons = {
            "ok": self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton),
            "fail": self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton),
            "warn": self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
        }

    # ------------------------ AES ------------------------

    def encrypt(self, data, key):
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return b64encode(cipher.nonce + tag + ciphertext)

    def decrypt(self, enc_data, key):
        data = b64decode(enc_data)
        nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

    # ------------------------ Check ------------------------

    def check_qmd(self):
        self.mode = "check"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open .qmd", "", "QMD Files (*.qmd)")
        if not path:
            return
        password, ok = QtWidgets.QInputDialog.getText(self, "Verification Key", "Enter verification key:")
        if not ok:
            return
        try:
            with open("keys.json", "r") as f:
                keys = json.load(f)
            file_key = keys.get(os.path.basename(path), {}).get("verify_key")
            if file_key != password:
                raise Exception("Invalid verification key!")
            with open(path, "rb") as f:
                enc = f.read()
                data = self.decrypt(enc, b64decode(keys[os.path.basename(path)]["decrypt_key"].encode()))
                self.file_hashes = json.loads(data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to verify .qmd: {e}")
            return
        self.list_widget.clear()
        for filepath, md5 in self.file_hashes.items():
            item = QtWidgets.QListWidgetItem(filepath)
            if not os.path.exists(filepath):
                item.setIcon(self.icons['warn'])
            else:
                if self.md5(filepath) == md5:
                    item.setIcon(self.icons['ok'])
                else:
                    item.setIcon(self.icons['fail'])
            self.list_widget.addItem(item)

    # ------------------------ Create ------------------------

    def create_qmd(self):
        self.mode = "create"
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select files or folder", "")
        if not files:
            return
        self.file_hashes = {}
        self.list_widget.clear()
        for f in files:
            item = QtWidgets.QListWidgetItem(f)
            self.list_widget.addItem(item)
            self.file_hashes[f] = self.md5(f)
        self.accept_btn.setVisible(True)

    # ------------------------ Edit ------------------------

    def edit_qmd(self):
        self.mode = "edit"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open .qmd", "", "QMD Files (*.qmd)")
        if not path:
            return
        password, ok = QtWidgets.QInputDialog.getText(self, "Decryption Key", "Enter FULL decryption key:")
        if not ok:
            return
        try:
            with open(path, "rb") as f:
                enc = f.read()
                data = self.decrypt(enc, b64decode(password.encode()))
                self.file_hashes = json.loads(data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to decrypt .qmd: {e}")
            return
        self.list_widget.clear()
        for filepath, md5 in self.file_hashes.items():
            item = QtWidgets.QListWidgetItem(filepath)
            self.list_widget.addItem(item)
        self.accept_btn.setVisible(True)

    # ------------------------ Save ------------------------

    def save_qmd(self):
        key1 = get_random_bytes(32)
        key2 = get_random_bytes(32)
        data = json.dumps(self.file_hashes).encode()
        enc = self.encrypt(data, key2)
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save .qmd", "", "QMD Files (*.qmd)")
        if not save_path:
            return
        with open(save_path, "wb") as f:
            f.write(enc)
        keys_file = "keys.json"
        try:
            with open(keys_file, "r") as f:
                keys = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            keys = {}

        keys[os.path.basename(save_path)] = {
            "verify_key": b64encode(key1).decode(),
            "decrypt_key": b64encode(key2).decode()
        }

        with open(keys_file, "w") as f:
            json.dump(keys, f, indent=4)

        QtWidgets.QMessageBox.information(self, "Keys",
            f"Verification Key:\n{b64encode(key1).decode()}\n\nFull Decryption Key:\n{b64encode(key2).decode()}")
        self.accept_btn.setVisible(False)

    # ------------------------ Tools ------------------------

    def add_file(self):
        if self.mode not in ("create", "edit"):
            QtWidgets.QMessageBox.warning(self, "Warning", "This function is only available in Create and Edit modes.")
            return
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Add files")
        for f in files:
            if f not in self.file_hashes:
                self.file_hashes[f] = self.md5(f)
                item = QtWidgets.QListWidgetItem(f)
                self.list_widget.addItem(item)

    def remove_selected(self):
        if self.mode not in ("create", "edit"):
            QtWidgets.QMessageBox.warning(self, "Warning", "This function is only available in Create and Edit modes.")
            return
        item = self.list_widget.currentItem()
        if item:
            filepath = item.text()
            self.file_hashes.pop(filepath, None)
            self.list_widget.takeItem(self.list_widget.row(item))

    def update_md5(self):
        if self.mode not in ("create", "edit"):
            QtWidgets.QMessageBox.warning(self, "Warning", "This function is only available in Create and Edit modes.")
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            filepath = item.text()
            if os.path.exists(filepath):
                self.file_hashes[filepath] = self.md5(filepath)
        QtWidgets.QMessageBox.information(self, "MD5 Updated", "MD5 hashes has successfully updated.")

    # ------------------------ Utils ------------------------

    def md5(self, filepath):
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            while chunk := f.read(4096):
                h.update(chunk)
        return h.hexdigest()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = QuickMD()
    window.show()
    sys.exit(app.exec())
