import sys, os, hashlib, json, requests, zipfile, shutil, tempfile
from PyQt6 import QtWidgets, QtGui, QtCore

_version = "28 May 2025"

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
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_list)
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.button_layout.addWidget(self.accept_btn)
        self.button_layout.addWidget(self.clear_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.close_btn)
        self.layout.addLayout(self.button_layout)

        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction("Check .qmd", self.check_qmd)
        file_menu.addSeparator()
        file_menu.addAction("Create .qmd", self.create_qmd)
        file_menu.addAction("Create .qmd (full folder)", self.create_qmd_folder)
        file_menu.addAction("Edit .qmd", self.edit_qmd)

        edit_menu = self.menuBar().addMenu("Tools")
        edit_menu.addAction("Add file", self.add_file)
        edit_menu.addAction("Remove selected", self.remove_selected)
        edit_menu.addAction("Edit selected path", self.edit_selected_path)
        edit_menu.addAction("Update md5", self.update_md5)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("How to use", self.show_how_to_use)
        help_menu.addAction("About", self.show_about)
        help_menu.addSeparator()
        help_menu.addAction("Check For Updates", self.check_for_update)

        self.icons = {
            "ok": self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton),
            "fail": self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton),
            "warn": self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
        }

    # ------------------------ Check ------------------------

    def check_qmd(self):
        self.mode = "check"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open .qmd", "", "QMD Files (*.qmd)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                self.file_hashes = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open .qmd: {e}")
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
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select files", "")
        if not files:
            return
        self.file_hashes = {}
        self.list_widget.clear()
        for f in files:
            item = QtWidgets.QListWidgetItem(f)
            self.list_widget.addItem(item)
            self.file_hashes[f] = self.md5(f)
        self.accept_btn.setVisible(True)

    def create_qmd_folder(self):
        self.mode = "create"
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder to create .qmd")
        if not folder:
            return

        choice, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Trim Path",
            "Select path style:",
            ["Full Path", "Relative to selected folder", "File Name Only"],
            1,  # default = relative
            False
        )

        if not ok:
            return

        self.file_hashes = {}
        self.list_widget.clear()

        for root, dirs, files in os.walk(folder):
            for file in files:
                full_path = os.path.normpath(os.path.join(root, file))

                if choice == "Full Path":
                    display_path = full_path
                elif choice == "Relative to selected folder":
                    display_path = os.path.relpath(full_path, folder)
                elif choice == "File Name Only":
                    display_path = file
                else:
                    display_path = full_path  # fallback

                item = QtWidgets.QListWidgetItem(display_path)
                self.list_widget.addItem(item)
                self.file_hashes[display_path] = self.md5(full_path)

        QtWidgets.QMessageBox.information(self, "Folder Loaded", f"Loaded {len(self.file_hashes)} files.")
        self.accept_btn.setVisible(True)

    # ------------------------ Edit ------------------------

    def edit_qmd(self):
        self.mode = "edit"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open .qmd", "", "QMD Files (*.qmd)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                self.file_hashes = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open .qmd: {e}")
            return
        self.list_widget.clear()
        for filepath in self.file_hashes:
            item = QtWidgets.QListWidgetItem(filepath)
            self.list_widget.addItem(item)
        self.accept_btn.setVisible(True)

    # ------------------------ Save ------------------------

    def save_qmd(self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save .qmd", "", "QMD Files (*.qmd)")
        if not save_path:
            return
        try:
            with open(save_path, "w") as f:
                json.dump(self.file_hashes, f, indent=4)
            QtWidgets.QMessageBox.information(self, "Saved", "Successfully saved .qmd file.")
            self.accept_btn.setVisible(False)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save .qmd: {e}")

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

    def edit_selected_path(self):
        if self.mode not in ("create", "edit"):
            QtWidgets.QMessageBox.warning(self, "Warning", "This function is only available in Create and Edit modes.")
            return
        item = self.list_widget.currentItem()
        if item:
            old_path = item.text()
            new_path, ok = QtWidgets.QInputDialog.getText(self, "Edit Path", "Enter new file path:", text=old_path)
            if ok and new_path:
                if old_path in self.file_hashes:
                    self.file_hashes[new_path] = self.file_hashes.pop(old_path)
                    item.setText(new_path)

    def update_md5(self):
        if self.mode not in ("create", "edit"):
            QtWidgets.QMessageBox.warning(self, "Warning", "This function is only available in Create and Edit modes.")
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.text()
            if os.path.exists(path):
                self.file_hashes[path] = self.md5(path)
        QtWidgets.QMessageBox.information(self, "Update", "MD5 hashes updated.")

    # ------------------------ Utils ------------------------

    def show_how_to_use(self):
        how_to_use = QtWidgets.QDialog(self)
        how_to_use.setWindowTitle("How To Use QuickMD")
        how_to_use.setFixedSize(500, 400)

        layout = QtWidgets.QVBoxLayout(how_to_use)

        info_label = QtWidgets.QLabel()
        info_label.setText(
            "QuickMD — a tool for creating, verifying, and editing .qmd files (JSON with file checksums).<br><br>"
            "Features:<br>"
            "- File > Check .qmd — verify the integrity of files using a .qmd file.<br>"
            "- File > Create .qmd — create a .qmd file for selected files.<br>"
            "- File > Create .qmd (full folder) — create a .qmd file for all files in a folder.<br>"
            "- File > Edit .qmd — open and edit a .qmd file.<br><br>"
            "Additional (available in Create and Edit modes):<br>"
            "- Tools > Add file — add a file.<br>"
            "- Tools > Remove selected — remove the selected file.<br>"
            "- Tools > Edit selected path — edit the file path.<br>"
            "- Tools > Update md5 — update MD5 hashes for all files.<br><br>"
            "When creating or editing, click 'Accept' after making changes to save the .qmd file.<br>"
            "The 'Clear' button clears the file list without saving.<br>"
            "The 'Close' button closes the program."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(info_label)

        how_to_use.exec()

    def show_about(self):
        about = QtWidgets.QDialog(self)
        about.setWindowTitle("About QuickMD")
        about.setFixedSize(400, 200)

        layout = QtWidgets.QVBoxLayout(about)

        info_label = QtWidgets.QLabel()
        info_label.setText(
            '<b><h1>QuickMD</h1></b>'
            'Build: 28 May 2025<br>'
            '© 2025 eachcart<br><br>'
            'QuickMD is a fast and simple tool for .qmd packaging.<br>'
            'Licensed under <a href="https://github.com/eachcart/ePL/blob/main/README.md">ePL.</a><br><br>'
            '<a href="https://github.com/eachcart/quickmd">Github</a> <a href="https://t.me/eachcart">Telegram</a>'
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(info_label)

        about.exec()

    def clear_list(self):
        self.list_widget.clear()
        self.file_hashes = {}
        QtWidgets.QMessageBox.information(self, "Cleared", "The list has been cleared.")
        self.accept_btn.setVisible(False)

    def md5(self, path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    # ----------------------- Updates -----------------------

    def update(self):
        try:
            tmp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(tmp_dir, "qmd.zip")
            with requests.get("https://notype.ru/qmd.zip", stream=True) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
            bak_dir = os.path.join(current_dir, "bak")
            if os.path.exists(bak_dir):
                shutil.rmtree(bak_dir)
            os.rename(current_dir, bak_dir)
            shutil.move(tmp_dir, current_dir)

            QtWidgets.QMessageBox.information(None, "Update", "Updated successfully. Please restart the app.")
            sys.exit(0)

        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error", f"Update failed: {e}")
            sys.exit(1)

    def check_for_update(self):
        try:
            r = requests.get("https://notype.ru/qmd.version")
            r.raise_for_status()
            remote_version = r.text.strip()
            if remote_version != _version:
                reply = QtWidgets.QMessageBox.question(
                    None, "Update Available", 
                    f"New version ({remote_version}) available. Update now?", 
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    update()
            elif remote_version == _version:
                QtWidgets.QMessageBox.question(
                    None, "No latest updates found", 
                    f"Your version: {_version}", 
                    QtWidgets.QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            print("Update check failed:", e)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = QuickMD()
    window.show()
    sys.exit(app.exec())
