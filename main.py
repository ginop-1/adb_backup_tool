import sys, subprocess
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QCheckBox, QMessageBox
from ui.window import Ui_MainWindow


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        self.dirs: list[QCheckBox] = []

    def connectSignalsSlots(self):
        self.actionread_ADB_devices.triggered.connect(self.read_ADB_devices)
        self.backupBtn.clicked.connect(self.backup)

    def spawn_dialog(self, message: str, type: str = "Information"):
        msg = QMessageBox()
        if type == "Information":
            msg.setIcon(QMessageBox.Information)
        elif type == "Critical":
            msg.setIcon(QMessageBox.Critical)
        elif type == "Warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "Question":
            msg.setIcon(QMessageBox.Question)
        # setting message for Message Box
        msg.setText(message)
        # declaring buttons on Message Box
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.update_dirs()
        # start the app
        msg.exec_()


    def read_ADB_devices(self):
        self.dirs.clear()
        self.dirsSelection.clear()
        self.dirsSelected.clear()
        self.update_dirs()

        try:
            raw_dirs: list[str] = subprocess.check_output(['adb', 'shell', 'ls', '-a', '/sdcard/'], stderr=subprocess.STDOUT).decode('utf-8').split('\n')
            print(raw_dirs)
        except subprocess.CalledProcessError as error:
            self.spawn_dialog(error.output.decode('utf-8'), type="Critical")
            return
        
        if self.dirsSelection.layout() is None:
            self.dirsSelection.setLayout(QVBoxLayout())
            self.dirsSelected.setLayout(QVBoxLayout())
        
        self.update_dirs(layout=True)

        for i, dir in enumerate(raw_dirs):
            if not dir:
                continue
            self.dirs.append(QCheckBox(dir))
            self.dirsSelection.layout().addWidget(self.dirs[i])
            self.dirs[i].stateChanged.connect(partial(self.dirs_state_changed, i))
        
        self.dirsSelection.layout().addStretch()
        self.dirsSelected.layout().addStretch()
        
    def update_dirs(self, layout: bool = False):
        self.dirsSelection.update()
        self.dirsSelected.update()
        if layout:
            self.dirsSelection.layout().update()
            self.dirsSelected.layout().update()

    def dirs_state_changed(self, n: int):
        if self.dirs[n].checkState():
            # Add to selected
            self.dirsSelected.addItem(self.dirs[n].text())
        else:
            # Remove from selected
            for i in range(self.dirsSelected.count()):
                if self.dirsSelected.item(i).text() == self.dirs[n].text():
                    self.dirsSelected.takeItem(i)
                    break
        self.update_dirs()

    def backup(self):
        if not self.dirsSelected.count():
            self.spawn_dialog("No directories selected", type="Warning")
            return
        try:
            for i in range(self.dirsSelected.count()):
                subprocess.check_output(['adb', 'pull', '/sdcard/' + self.dirsSelected.item(i).text(), './bkp/' + self.dirsSelected.item(i).text()], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            self.spawn_dialog(error.output.decode('utf-8'), type="Critical")
            return
        self.spawn_dialog("Backup complete", type="Information")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())