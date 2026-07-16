import win32gui
from win32con import *
from test import *
import win32api
import pyperclip
import time
from pywinauto import Application
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)

class UIController:
    def __init__(self, dlg):
        self.current_path = None
        self.dlg = dlg
        self.main_handle = dlg.handle
        self.you_have_to_wait = 0.25 # 我没辙了
        self.pop_timeout = 1.0 # 窗口更新
        self.load_timeout = 60.0 # 数据加载
        self.wait_load_done = 0.5  # 窗口更新
        self.hwnd_dict = {
            "handle":[],
            "name":[],
            "snapshot":[]
        }

    def process(self, current_path):
        """
        跑一遍流程
        """
        self.current_path = current_path
        if not self.load():
            return False
        self.hide_all()
        return True


    def load(self):
        """
        复制路径到剪切板
        激活主窗口，Ctrl + V
        等待伪弹窗跳出
        激活伪弹窗，Enter
        等待
        """
        self.append_handle(self.main_handle)
        print_window_tree(self.main_handle)

        pyperclip.copy(self.current_path) # 复制到剪切板
        self.keyboard(self.main_handle,
                      VK_CONTROL, ord("V")) # Ctrl+ V 粘贴

        start = time.time()
        while win32gui.GetForegroundWindow() == self.main_handle:
            if time.time() - start > self.pop_timeout:
                return False
        pop_hwnd = win32gui.GetForegroundWindow() # 等待弹窗

        self.append_handle(pop_hwnd)
        print_window_tree(pop_hwnd)

        self.keyboard(pop_hwnd,
                      VK_RETURN) # Enter 确认

        start = time.time()
        while time.time() - start < self.load_timeout:  # 等待项目加载
            current_handle = win32gui.GetForegroundWindow()
            if current_handle != 0:
                if not current_handle in self.hwnd_dict["handle"] :
                    self.append_handle(current_handle)
                    if win32gui.GetWindowText(current_handle) == "向导": # 项目基本加载完了
                        time.sleep(self.wait_load_done)
                        return True
        return False

    def hide_all(self):
        """
        点击左上角收起 显示/隐藏 面板
        点击左上角收起 显示/隐藏 - 牙齿 面板
        Ctrl + 点击显示全部
        """
        show_hide_handle = self.handle_named("显示/隐藏组")
        left, top, right, bottom = win32gui.GetWindowRect(show_hide_handle)
        self.click(show_hide_handle, (left + 20,top + 20))

    def activate_window(self, handle):
        """
        目前来说，窗口激活是必要的。
        后台办法我验证过了，
        基本不行
        已经努力避免抢夺鼠标了
        """
        win32gui.ShowWindow(handle, SW_RESTORE)
        win32gui.SetForegroundWindow(handle)
        start = time.time()
        while time.time() - start < self.pop_timeout:
            time.sleep(self.you_have_to_wait)
            if win32gui.GetForegroundWindow() == handle and win32gui.IsWindowEnabled(handle):
                break

    def keyboard(self, handle, *keys):
        """
        可以把快捷键事件看作
        后入先出的栈：
        {Ctrl 按下{ Shift 按下{ N 按下{} N 松开} Shift 松开} Ctrl 松开}
        """
        self.activate_window(handle)
        for key in keys:
            win32api.keybd_event(key, 0, 0, 0)
        for key in reversed(keys):
            win32api.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)

    def click(self, handle, pos):
        """
        妥协了。真的得用鼠标
        """
        self.activate_window(handle)
        old_pos = win32api.GetCursorPos()
        win32api.SetCursorPos(pos)
        win32api.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        win32api.SetCursorPos(old_pos)

    def append_handle(self, handle):
        self.hwnd_dict["handle"].append(handle)
        self.hwnd_dict["name"].append(win32gui.GetWindowText(handle))
        self.hwnd_dict["snapshot"].append((get_window_snapshot(handle)))

    def handle_named(self, name, key_type="handle"):
        if name in self.hwnd_dict["name"]:
            return self.hwnd_dict[key_type][self.hwnd_dict["name"].index(name)]
        return False


