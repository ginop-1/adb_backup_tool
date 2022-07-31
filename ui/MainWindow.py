import subprocess
from functools import partial
from tabnanny import check
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QCheckBox
from PyQt5.QtCore import QThread, QTimer

from .generated.window import Ui_MainWindow
from .utils import BackupWorker, spawn_dialog, AdbHelper


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        self.dirs: list[QCheckBox] = []
        self.statusbar.showMessage("Searching for ADB devices...")
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_ADB_devices)
        self.read_ADB_devices()

    def connectSignalsSlots(self):
        self.actionread_ADB_devices.triggered.connect(self.read_ADB_devices)
        self.backupBtn.clicked.connect(self.backup)

    def clear(self):
        for checkbox in self.dirs:
            checkbox.deleteLater()
        self.dirs.clear()
        self.update_dirs()

    def read_ADB_devices(self):
        self.dirs.clear()
        self.dirsSelection.clear()
        self.dirsSelected.clear()
        self.update_dirs()

        try:
            raw_dirs = AdbHelper.get_dirs()
        except subprocess.CalledProcessError as error:
            spawn_dialog(error.output.decode('utf-8'), type="Critical")
            self.clear()
            return
        device_infos = AdbHelper.get_device_infos()
        self.statusbar.showMessage(
            "Device found. Model: " + device_infos["model"] +
            ", Android Version: " + device_infos["android_version"] +
            ", Id: " + device_infos["id"]
        )

        if self.dirsSelection.layout() is None:
            self.dirsSelection.setLayout(QVBoxLayout())
            self.dirsSelected.setLayout(QVBoxLayout())

        self.timer.stop()
        self.update_dirs(layout=True)
        
        for i, dir in enumerate(raw_dirs):
            if not dir or dir == '.' or dir == '..' or dir.startswith("* daemon "):
                # TODO: That's a hack, fix it
                continue
            self.dirs.append(QCheckBox(dir))
            self.dirsSelection.layout().addWidget(self.dirs[i])
            self.dirs[i].stateChanged.connect(
                partial(self.dirs_state_changed, i)
            )

        self.dirsSelection.layout().addStretch()
        self.dirsSelected.layout().addStretch()

    def update_dirs(self, layout: bool = False):
        self.dirsSelection.update()
        self.dirsSelected.update()
        if layout:
            self.dirsSelection.layout().update()
            self.dirsSelected.layout().update()
        self.show()

    def update_statusbar(self, message: str):
        self.statusbar.showMessage(message)

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
            spawn_dialog("No directories selected", type="Warning")
            return

        self.thread = QThread()
        self.worker = BackupWorker(self.dirsSelected)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_statusbar)
        self.thread.start()

        self.thread.finished.connect(
            lambda: self.update_statusbar("Backup finished")
        )
        self.thread.finished.connect(
            lambda: spawn_dialog("Backup finished", type="Information")
        )
        self.thread.finished.connect(
            self.read_ADB_devices
        )
        
        self.worker.stop()
