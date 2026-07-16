from UIController import UIController
from pywinauto import Application
import subprocess
import pygetwindow as gw
import time
import os

class BatchExporter:
    def __init__(self, exe_path, title_keyword, timeout):
        self.exe_path = exe_path
        self.loading = False
        self.app = None
        self.dlg = None
        self.timeout = timeout
        self.title_keyword = title_keyword
        self.init_success = False
        self.file_type = "dentalProject"
        self.UIController = None

    def init(self):
        """
        启动 EXOCAD 进程，
        不需要每个循环都启动，
        不然每次开启关闭的时间开销太大了
        """
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            all_windows = gw.getAllTitles()
            for title in all_windows:
                if self.title_keyword in title: # 确保UI窗口已开。后半句其实没用，以防万一
                    self.loading = False
                    self.init_success = True
                    self.app = Application(backend="win32").connect(title=title) # 用不了uia
                    self.dlg = self.app.window(title=title)
                    self.UIController = UIController(self.dlg)
                    return self.init_success
            if not self.app and not self.loading:
                self.loading = True
                subprocess.Popen([self.exe_path], shell=True)
                print("new process generate")
        return self.init_success

    def start(self, root_path):
        """
        路径遍历。
        以后有需求的话
        我给它做个配套的UI
        """
        if self.init_success and self.UIController:
            for sub_name in os.listdir(root_path):
                sub_path = root_path + "\\" + sub_name
                if os.path.isdir(sub_path):
                    for file_name in os.listdir(sub_path):
                        if self.file_type in file_name:
                            file_path = sub_path + "\\" + file_name
                            # self.UIController.process(file_path)
                            print(self.UIController.process(file_path))
                            return

    def close(self):
        """
        关不关都无所谓，不差这个
        """
        if self.dlg:
            pid = self.dlg.process_id
            subprocess.call(["TASKKILL", "/PID", str(pid), "/F"], shell=True)
