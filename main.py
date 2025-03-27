import sys
import os
import hashlib
import json
from PyQt6 import QtWidgets, QtGui, QtCore

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
        menu.addAction("Unpack .qmd", self.unpack_qmd)

        edit_menu = self.menuBar().addMenu("Tools")
        edit_menu.addAction("Add file", self.add_file)
        edit_menu.addAction("Remove selected", self.remove_selected)
        edit_menu.addAction("Edit selected path", self.edit_selected_path)
        edit_menu.addAction("Update md5", self.update_md5)

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

    # ------------------------ Unpack ------------------------

    def unpack_qmd(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open .qmd to Unpack", "", "QMD Files (*.qmd)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                file_hashes = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open .qmd: {e}")
            return

        try:
            list_path = os.path.splitext(path)[0] + ".qmdu"
            with open(list_path, "w") as f:
                for filepath, md5 in file_hashes.items():
                    f.write(f"{filepath}:{md5}\n")
            QtWidgets.QMessageBox.information(self, "Unpack", f"Unpacked hashes to {list_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to unpack: {e}")

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

    def md5(self, path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = QuickMD()
    window.show()
    sys.exit(app.exec())
