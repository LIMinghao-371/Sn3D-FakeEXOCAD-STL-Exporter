from util import *
import win32api
import pyperclip
import time

class UIController:
    def __init__(self, dlg):
        # 主窗口句柄，要复用，不能清除
        self.dlg = dlg
        self.main_handle = dlg.handle
        # 可以清除
        self.current_path = None
        self.hwnd_dict = {
            "handle":[],
            "name":[],
            "snapshot":[]
        }
        # 只读，无须清除
        self.eye_imp_path = "icon/eye.png"
        self.search_imp_path = "icon/search.png"
        self.pop_timeout = 1.0 # 窗口更新
        self.clear_timeout = 2.0  # 窗口更新
        self.load_timeout = 60.0 # 数据加载
        self.you_have_to_wait = 0.25 # 我没辙了
        self.wait_load_done = 0.5  # 加载延迟
        self.wait_ui_done = 0.5  # UI更新
        self.wait_click_done = 0.15  # 点击延迟
        self.close_bias = (0, -10)
        self.hide_all_bias = (-120, -20)
        self.eye_bar_bias = (25, 20, 55, -20)
        self.eye_click_bias = (30, 0)
        self.search_bar_bias = (0, 0, 60, 0)
        self.black_list = []

    def process(self, current_path):
        """
        跑一遍流程
        """
        self.current_path = current_path
        if not self.load():
            return False
        # if not self.hide_all():
        #     return False
        # if not self.key_judge(ord("M")): # Merge 合并
        #     return False
        # if not self.right_menu(ord("A")): # Articulation 我猜的，对颌牙
        #     return False
        return True


    def load(self):
        """
        复制路径到剪切板
        激活主窗口，Ctrl + V
        等待伪弹窗跳出
        激活伪弹窗，Enter
        等待
        """
        try:
            self.append_handle(self.main_handle)

            pyperclip.copy(self.current_path) # 复制到剪切板
            self.keyboard(self.main_handle,
                          VK_CONTROL, ord("V")) # Ctrl+ V 粘贴

            start = time.time()
            while time.time() - start < self.pop_timeout:
                if (win32gui.GetForegroundWindow() != self.main_handle
                        and win32gui.GetForegroundWindow() != 0):
                    break

            time.sleep(self.wait_ui_done)


            pop_hwnd = win32gui.GetForegroundWindow() # 等待弹窗
            print_window_tree(pop_hwnd)
            self.append_handle(pop_hwnd)
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
        except Exception as e:
            print(e)
            return False

    def hide_all(self):
        """
        点击左上角收起 显示/隐藏 面板 (测试一下)
        Ctrl + 点击 隐藏全部
        点击右上角展开 显示/隐藏 面板 (测试一下)
        """
        try:
            show_hide_handle = self.handle_named("显示/隐藏组")
            left, top, right, bottom = win32gui.GetWindowRect(show_hide_handle)
            self.click(show_hide_handle,
                       (right + self.hide_all_bias[0],
                        bottom + self.hide_all_bias[1]), True)
            start = time.time()
            while time.time() - start < self.pop_timeout:
                if not self.match(self.handle_named("显示/隐藏组"),
                                  self.eye_bar_bias,
                                  self.eye_imp_path):
                    break
            return True
        except Exception as e:
            print(e)
            return False

    def key_judge(self, key):
        """
        检测是否有 某个数据？
        点击 键盘对应按键
        如果对应小眼睛亮了，说明有
        """
        try:
            handle = self.main_handle
            self.keyboard(handle,
                          key)
            time.sleep(self.wait_ui_done)
            result = self.match(self.handle_named("显示/隐藏组"),
                                self.eye_bar_bias,
                                self.eye_imp_path)
            self.keyboard(handle,
                          key)
            time.sleep(self.wait_ui_done)
            if result["found"]:
                return result
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def right_menu(self, key):
        """
        点击 键盘对应按键
        如果对应小眼睛亮了，说明有数据
        右键 小眼睛
        跳出右键菜单
        搜索栏输入 功能菜单
        Enter
        下一步：单个直接保存/ 多个列表选择保存
        """
        try:
            show_hide_handle = self.handle_named("显示/隐藏组")
            current_root_handle = win32gui.GetForegroundWindow()
            eye_result = self.key_judge(key)
            assume_one_task = True
            assume_task_num = 1
            loop_num = 0
            if type(eye_result) == dict:
                pos = eye_result["center"]
                while loop_num < assume_task_num:
                    self.click(show_hide_handle,
                               (pos[0] + self.eye_click_bias[0],
                                pos[1] + self.eye_click_bias[1]), button = "right", back = False)

                    current_handle = None
                    start = time.time()
                    while time.time() - start < self.pop_timeout:
                        current_handle = win32gui.GetForegroundWindow()
                        if (current_handle != current_root_handle
                                and current_handle != show_hide_handle):
                            break

                    if current_handle:
                        pyperclip.copy("功能菜单")
                        self.keyboard(current_handle,
                                      VK_CONTROL, ord("V"))
                        time.sleep(self.wait_ui_done)

                        before = get_all_top_hwnds()

                        self.keyboard(current_handle,
                                      VK_RETURN)
                        time.sleep(self.wait_ui_done)

                        after = get_all_top_hwnds()
                        new_handles = after - before
                        target_hwnd = None
                        search_result = {}
                        task_height = None
                        for hwnd in new_handles:
                            rect = win32gui.GetWindowRect(hwnd)
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                            title = win32gui.GetWindowText(hwnd)
                            if width > 100 and height > 50 and title == "": # 很怪 但是这个判断方式确实不错
                                search_result = self.match(hwnd, # 单个数据
                                           self.search_bar_bias,
                                           self.search_imp_path)
                                target_hwnd = hwnd
                                task_height = height
                                break
                        if target_hwnd is None or search_result is {}:
                            return False
                        else:
                            loop_num += 1
                            if assume_one_task:
                                if search_result["found"]: # 单个数据
                                    self.selector(target_hwnd, 0)
                                elif task_height is not None: # 多个数据
                                    assume_one_task = False
                                    assume_task_num = int((task_height - 4) / 50) # 只要他不改UI高度这就是最准的
                                    self.selector(target_hwnd, loop_num)
                            else:
                                self.selector(target_hwnd, loop_num)
                    else:
                        return False
                if loop_num == 0:
                    return False
                else:
                    return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def selector(self, hwnd, num):
        try:
            if num > 0:
                active = True
                for i in range(num):
                    self.keyboard(hwnd, VK_DOWN, activate=active)
                    active = False
                self.keyboard(hwnd, VK_RIGHT, activate=False)
            elif num == 0:
                self.keyboard(hwnd, VK_DOWN)
            for i in range(2):
                self.keyboard(hwnd, VK_DOWN, activate=False)
            self.keyboard(hwnd, VK_RETURN)
            self.saver()
            return True
        except Exception as e:
            print(e)
            return False

    def saver(self):
        try:
            save_handle = None
            start = time.time()
            while time.time() - start < self.wait_ui_done:
                hwnd = win32gui.FindWindow("#32770", None)
                if hwnd:
                    title = win32gui.GetWindowText(hwnd)
                    if "保存" in title:
                        save_handle = hwnd
                        break
            if save_handle is not None:
                pyperclip.copy("里面好.stl") # 命名规则 ########
                self.keyboard(save_handle,
                              VK_CONTROL, ord("V"))
                self.keyboard(save_handle,
                              VK_RETURN)
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def match(handle, bias, imp_path):
        """
        限定范围内
        匹配图案
        """
        try:
            left, top, right, bottom = win32gui.GetWindowRect(handle)
            rect = (left + bias[0],
                    top + bias[1],
                    left + bias[2],
                    bottom + bias[3])
            result = match_template_in_rect(rect, imp_path)
            return result
        except Exception as e:
            print(e)
            return False

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

    def keyboard(self, handle, *keys, activate = True):
        """
        可以把快捷键事件看作
        后入先出的栈：
        {Ctrl 按下{ Shift 按下{ N 按下{} N 松开} Shift 松开} Ctrl 松开}
        """
        if activate:
            self.activate_window(handle)
        for key in keys:
            win32api.keybd_event(key, 0, 0, 0)
        for key in reversed(keys):
            win32api.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)

    def click(self, handle, pos, ctrl = False, button = "left", back = True):
        """
        妥协了。真的得用鼠标
        """
        if button == "left":
            down_event = MOUSEEVENTF_LEFTDOWN
            up_event = MOUSEEVENTF_LEFTUP
        else:
            down_event = MOUSEEVENTF_RIGHTDOWN
            up_event = MOUSEEVENTF_RIGHTUP
        self.activate_window(handle)
        old_pos = win32api.GetCursorPos()
        win32api.SetCursorPos(pos)
        if ctrl:
            win32api.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(self.wait_click_done)
        win32api.mouse_event(down_event, 0, 0, 0, 0)
        win32api.mouse_event(up_event, 0, 0, 0, 0)
        if ctrl:
            win32api.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        if back:
            win32api.SetCursorPos(old_pos)

    def append_handle(self, handle):
        self.hwnd_dict["handle"].append(handle)
        self.hwnd_dict["name"].append(win32gui.GetWindowText(handle))
        self.hwnd_dict["snapshot"].append((get_window_snapshot(handle)))

    def handle_named(self, name, key_type="handle"):
        if name in self.hwnd_dict["name"]:
            return self.hwnd_dict[key_type][self.hwnd_dict["name"].index(name)]
        return False

    def clear(self):
        show_hide_handle = self.handle_named("显示/隐藏组")
        left, top, right, bottom = win32gui.GetWindowRect(show_hide_handle)
        current_root_handle = win32gui.GetForegroundWindow()

        self.click(show_hide_handle,
                   (left + self.close_bias[0],
                    top + self.close_bias[1]), button="right", back=False)

        current_handle = None
        start = time.time()
        while time.time() - start < self.pop_timeout:
            current_handle = win32gui.GetForegroundWindow()
            if (current_handle != current_root_handle
                    and current_handle != show_hide_handle):
                break
        if current_handle:
            pyperclip.copy("关闭")
            self.keyboard(current_handle,
                          VK_CONTROL, ord("V"))
            time.sleep(self.wait_ui_done)
            self.keyboard(current_handle,
                          VK_RETURN, activate=False)
            start = time.time()
            while time.time() - start < self.pop_timeout:
                current_handle = win32gui.GetForegroundWindow()
            self.keyboard(current_handle,
                          VK_RETURN)

        start = time.time()
        while time.time() - start < self.clear_timeout:
            if win32gui.GetWindowText(self.main_handle) == "exocad DentalCAD 3.3 Chemnitz 9512":
                break
        
        self.current_path = None
        self.hwnd_dict = {
            "handle": [],
            "name": [],
            "snapshot": []
        }


