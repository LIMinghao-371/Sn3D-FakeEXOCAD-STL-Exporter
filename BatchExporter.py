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
        name = []
        # name.append("001_高春峰" )  # 非法数据
        # name.append("1012罗志惠" )  # 超级非法数据
        # name.append("1003崔智森" )  # 报错了
        # name.append("1043曹忠厚1")  # 报错了
        # name.append("1015陈英琢" )  # 合并 单个牙齿，测试识别模式
        # name.append("1135毛晓燕" )  # 合并 多个基台，测试识别模式。 多个扫描杆。 牙龈 取舍。解刨形态。
        # name.append("1013郭佩琳" )  # 扫描模型 取舍。 ?<----
        # name.append("1107王奕麟" )  # 合并 单个基台，测试识别模式
        # name.append("1218谭卉"  )   # 合并 单个基台，测试识别模式
        # name.append("1207马凤良" )  # 多又全， 一个合并多个数据，有扫描杆
        # name.append("1187王宪英1")  # 合并，两颗牙 无扫描杆 一个解刨内冠，一个单颗合并
        # name.append("1040赵景波" )  # 合并，基台 和 修复体 <-- 合并部分菜单不对
        # name.append("1042夏德斌" )  # 合并，基台 和 修复体
        # name.append("1045韩金"  )   # 合并，只有单个基台，有扫描杆
        # name.append("1051李民"  )   # 合并，上下基台
        # name.append("1047闫"   )   # 两个 合并蜡型, 一个解刨内冠，一个合并
        # name.append("1006安成江"  ) # 报错
        # name.append("1013齐涣泽"  ) # 报错
        # name.append("1059张明明"  )  # 报错
        # name.append("1063蔡雨文"  )  # 报错
        if self.init_success and self.UIController:
            for sub_name in os.listdir(root_path):
                sub_path = root_path + "\\" + sub_name
                if os.path.isdir(sub_path):
                    for file_name in os.listdir(sub_path):
                        if self.file_type in file_name:
                            file_path = sub_path + "\\" + file_name
                            # if name is not None and sub_name not in name:
                            #     continue
                            # else:
                            #     name = None
                            result = self.UIController.process(file_path, sub_name)
                            self.UIController.todo(self.UIController.headers[13],self.UIController.clear)

    def close(self):
        """
        关不关都无所谓，不差这个
        """
        if self.dlg:
            pid = self.dlg.process_id
            subprocess.call(["TASKKILL", "/PID", str(pid), "/F"], shell=True)
