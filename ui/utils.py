import subprocess
from typing import Callable

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QListWidget, QMessageBox


def spawn_dialog(message: str, type: str = "Information", update_dirs: Callable = (lambda: None)):
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
    update_dirs()
    # start the app
    msg.exec_()


class BackupWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self, dirs: QListWidget) -> None:
        super().__init__()
        self.dirs = dirs
        self._isRunning = True

    def run(self):
        """Long-running task."""
        try:
            for i in range(self.dirs.count()):
                dir_name = self.dirs.item(i).text()
                self.progress.emit("Backing up... " + dir_name)
                subprocess.check_output(
                    ['adb', 'pull', '/sdcard/' + dir_name, './bkp/' + dir_name], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            spawn_dialog(error.output.decode('utf-8'), type="Critical")
            self.progress.emit("Error")
            return

        self.finished.emit()

    def stop(self):
        self._isRunning = False

    def flush(self):
        pass


class AdbHelper():
    def get_dirs() -> list[str]:
        return subprocess.check_output(
            ['adb', 'shell', 'ls', '-a', '/sdcard/'], stderr=subprocess.STDOUT).decode('utf-8').split('\n')

    def get_device_infos() -> dict[str: str]:
        # get phone id using "adb devices" command
        infos = {}
        infos["id"] = subprocess.check_output(["adb", "devices"]).decode('utf-8').split('\n')[1].split('\t')[0]
        infos["model"] = subprocess.check_output(["adb", "shell", "getprop", "ro.product.model"]).decode('utf-8').strip()
        infos["android_version"] = subprocess.check_output(["adb", "shell", "getprop", "ro.build.version.release"]).decode('utf-8').strip()
        return infos