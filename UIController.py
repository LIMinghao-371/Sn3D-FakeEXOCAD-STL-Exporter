from util import *
import win32api
import pyperclip
import time
import traceback
import re

class UIController:
    def __init__(self, dlg):
        # 主窗口句柄，要复用，不能清除
        self.dlg = dlg
        self.main_handle = dlg.handle
        # 可以清除
        self.current_type = None
        self.current_name = None
        self.current_path = None
        self.hwnd_dict = {
            "handle":[],
            "name":[],
            "snapshot":[]
        }
        self.name_list = []
        self.rename_list = []
        # 只读，无须清除
        self.eye_imp_path = "icon/_eye.png"
        self.search_imp_path = "icon/_search.png"
        self.group_dict = {
            "ScanPost": "icon/group-ScanPost.png",
        }
        self.white_dict = {
            "A": False,
            "S": "icon/txt-ScanModel.png",
            "ScanPost": False,
            "G": "icon/txt-Gingiva.png",
            "E": False,
        }
        self.name_key_dict = {
            "A": False,
            "S": False,
            "ScanPost": "icon/name-ScanPost.png",
            "G": False,
            "E": False,
        }
        self.database_dict = {
            "数据库模型信息": "牙形数据库",
            "植体替代体配置信息": "种植体数据库",
        }
        self.black_dict = {}
        self.pop_timeout = 1.0 # 窗口更新
        self.clear_timeout = 2.0  # 窗口更新
        self.load_timeout = 60.0 # 数据加载
        self.you_have_to_wait = 0.25 # 我没辙了
        self.wait_menu_done = 0.25  # 我没辙了
        self.wait_load_done = 0.5  # 加载延迟
        self.wait_ui_done = 0.5  # UI更新
        self.wait_click_done = 0.15  # 点击延迟
        self.close_bias = (0, -10)
        self.hide_all_bias = (-120, -20)
        self.eye_click_bias = (40, 0)
        self.eye_bar_bias = (25, 20, 55, -20)
        self.search_bar_bias = (0, 0, 60, 0)
        self.full_bias = (0, 0, -1, 0)


    def process(self, current_path, current_name):
        """
        跑一遍流程
        """
        self.current_path = current_path
        self.current_name = current_name
        if not self.load():
            return False
        if not self.hide_all():
            return False
        if not self.key_judge(ord("M")): # M for Merged parts 合并
            return False
        # if not self.to_save(key="A"): # A for Antagonist 对颌牙
        #     return False
        # if not self.to_save(key="S"): # S for Jaw Scans 扫描模型
        #     return False
        # if not self.to_save(group="ScanPost", name_from_database="数据库模型信息"): # 没有对应快捷键 扫描杆
        #     return False
        # if not self.to_save(key="G"): # G for Gingiva scans 牙龈扫描
        #     return False
        if not self.to_save(key="E"): # E for Anatomic parts 解剖形态
            return False
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
            log("load: time out")
            return False
        except Exception as e:
            log("class UIController.load Error\n",traceback.format_exc())
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
            log("class UIController.hide_all Error\n",traceback.format_exc())
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
            return result
        except Exception as e:
            log("class UIController.key_judge Error\n",traceback.format_exc())
            return False

    def to_save(self, key = None, group = None, name_from_database = None):
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
            self.name_list = []
            if key is not None:
                eye_result = self.key_judge(ord(key))
                self.current_type = key
            elif group is not None:
                eye_result = self.match(show_hide_handle,
                                        self.full_bias,
                                        self.group_dict[group])
                self.current_type = group
            else:
                self.current_type = None
                log("to_save: no key no group")
                return False
            assume_one_task = True
            assume_task = [1]
            loop_num = 0
            if type(eye_result) == dict:
                pos = eye_result["center"]
                if name_from_database is not None:
                    right_call_handle = self.call_right_menu(show_hide_handle,  # 右键，唤起右键菜单
                                                          pos,
                                                          [show_hide_handle, current_root_handle])
                    if right_call_handle:
                        pyperclip.copy(name_from_database) # 搜索功能菜单
                        self.keyboard(right_call_handle,
                                      VK_CONTROL, ord("V"))
                        time.sleep(self.wait_ui_done)
                        self.keyboard(right_call_handle,
                                      VK_RETURN)
                        start = time.time()
                        data = None
                        while time.time() - start < self.pop_timeout:
                            current_handle = win32gui.GetForegroundWindow()
                            if win32gui.GetWindowText(current_handle) == self.database_dict[name_from_database]:
                                self.keyboard(current_handle,
                                              VK_CONTROL, ord("C"))
                                time.sleep(self.wait_click_done)
                                data = pyperclip.paste()
                                self.keyboard(current_handle,
                                              VK_RETURN)
                                break
                        self.name_list = self.get_name_list(data)
                while loop_num < len(assume_task):
                    right_call_handle = self.call_right_menu(show_hide_handle, # 右键，唤起右键菜单
                                                          pos,
                                                          [show_hide_handle, current_root_handle])
                    if right_call_handle:
                        time.sleep(self.wait_click_done)
                        pyperclip.copy("功能菜单") # 搜索功能菜单
                        self.keyboard(right_call_handle,
                                      VK_CONTROL, ord("V"))
                        time.sleep(self.wait_ui_done)
                        target_hwnd, search_result, task_top, task_bottom = self.check_new_pop(right_call_handle) # 点击，检测新窗口
                        if target_hwnd is None and search_result is None:
                            log("to_save: no target_hwnd no search_result")
                            return False
                        else:
                            if assume_one_task:
                                if search_result is not False: # 单个数据
                                    self.selector(target_hwnd, 0)
                                elif task_top is not None and task_bottom is not None: # 多个数据
                                    assume_one_task = False
                                    assume_task = self.get_task(target_hwnd, task_top, task_bottom, key, group)
                                    if len(assume_task) > 0:
                                        self.selector(target_hwnd, assume_task[loop_num])
                                    else:
                                        log("to_save: len(assume_task) == 0")
                                        return False
                            else:
                                self.selector(target_hwnd, assume_task[loop_num])
                            loop_num += 1
                    else:
                        log("to_save: no right call window handle")
                        return False
                if loop_num == 0:
                    log("to_save: no data saved")
                    return False
                else:
                    return True
            else:
                log("to_save: no eye result")
                return False
        except Exception as e:
            log("class UIController.to_save Error\n",traceback.format_exc())
            return False

    def call_right_menu(self, handle, pos, sub_handles):
        try:
            self.click(handle,
                       (pos[0] + self.eye_click_bias[0],
                        pos[1] + self.eye_click_bias[1]), button="right", back=False)
            start = time.time()
            while time.time() - start < self.pop_timeout:
                current_handle = win32gui.GetForegroundWindow()
                if current_handle not in sub_handles:
                    return current_handle
            log("call_right_menu: time out")
            return False
        except Exception as e:
            log("class UIController.call_right_menu Error\n",traceback.format_exc())
            return False

    def check_new_pop(self, handle):
        before = get_all_top_hwnds()

        self.keyboard(handle,
                      VK_RETURN)
        time.sleep(self.wait_menu_done)

        after = get_all_top_hwnds()

        new_handles = after - before
        target_hwnd = None
        search_result = None
        task_top = None
        task_bottom = None
        for hwnd in new_handles:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            title = win32gui.GetWindowText(hwnd)
            if width > 100 and height > 50 and title == "":  # 很怪 但是这个判断方式确实不错
                search_result = self.match(hwnd,  # 单个数据
                                           self.search_bar_bias,
                                           self.search_imp_path)
                target_hwnd = hwnd
                task_top = rect[1]
                task_bottom = rect[3]
                break
        return target_hwnd, search_result, task_top, task_bottom

    def get_task(self, target_hwnd, task_top, task_bottom, key, group):
        if key is not None:
            white_name = self.white_dict[key]
            key_name = self.name_key_dict[key]
        elif group is not None:
            white_name = self.white_dict[group]
            key_name = self.name_key_dict[group]
        else:
            return []

        if white_name:
            match_results = self.match(target_hwnd,  # 单个数据
                                       self.full_bias,
                                       white_name,
                                       all_result=True)
            if match_results is not False:
                assume_task = self.target_chooser(match_results, task_top + 2, task_bottom - 2)
            else:
                assume_task = []
        else:
            assume_task = list(range(1, int((task_bottom - task_top - 2) / 50) + 1))

        if key_name:
            match_results = self.match(target_hwnd,  # 单个数据
                                       self.full_bias,
                                       key_name,
                                       all_result=True)
            if match_results is not False:
                rename_task = self.target_chooser(match_results, task_top + 2, task_bottom - 2)
                self.rename_list = sorted(set(rename_task) & set(assume_task))
            else:
                self.rename_list = []

        return assume_task

    @staticmethod
    def target_chooser(match_results, top, bottom, step=50):
        boundaries = list(range(top, bottom, step))
        if boundaries[-1] < bottom:
            boundaries.append(bottom)
        values = []
        for match_result in match_results:
            values.append(match_result['center'][1])
        results = []
        for val in values:
            idx = -1
            for i in range(len(boundaries) - 1):
                if boundaries[i] <= val < boundaries[i + 1]:
                    idx = i + 1
                    break
            if idx != -1:
                results.append(idx)
        return sorted(results)

    def selector(self, hwnd, num):
        try:
            if num > 0:
                active = True
                for i in range(num):
                    self.keyboard(hwnd, VK_DOWN, activate=active)
                    active = False
                self.keyboard(hwnd, VK_RIGHT, activate=False)
            elif num == 0:
                self.keyboard(hwnd, VK_UP)
            self.keyboard(hwnd, VK_UP, activate=False)
            time.sleep(self.wait_menu_done)
            self.keyboard(hwnd, VK_RETURN)
            self.saver(num)
            return True
        except Exception as e:
            log("class UIController.selector Error\n",traceback.format_exc())
            return False

    def saver(self, num):
        try:
            save_handle = None
            default_name = ""
            start = time.time()
            while time.time() - start < self.pop_timeout:
                hwnd = win32gui.FindWindow("#32770", None)
                if hwnd:
                    title = win32gui.GetWindowText(hwnd)
                    if "保存" in title:
                        result = get_filename_edit_handle(hwnd)
                        if result:
                            default_name = result
                            save_handle = hwnd
            if save_handle is not None:
                new_name = self.rename(default_name, self.current_name, num)
                pyperclip.copy(new_name)
                self.keyboard(save_handle,
                              VK_CONTROL, ord("V"))
                self.keyboard(save_handle,
                              VK_RETURN)

                output_message = ": 已保存"
                start = time.time()
                while time.time() - start < self.pop_timeout:
                    hwnd = win32gui.FindWindow("#32770", None)
                    title = win32gui.GetWindowText(hwnd)
                    if "确认另存为" in title:
                        time.sleep(self.wait_click_done)
                        self.keyboard(save_handle,
                                      VK_LEFT, activate=False)
                        self.keyboard(save_handle,
                                      VK_RETURN, activate=False)
                        output_message = ": 已覆盖"
                        break
                log(new_name, output_message)
                start = time.time()
                while time.time() - start < self.pop_timeout:
                    hwnd = win32gui.FindWindow("#32770", None)
                    if not hwnd or not "保存" in win32gui.GetWindowText(hwnd):
                        time.sleep(self.wait_click_done)
                        break
                return True
            else:
                log("saver: no save handle")
                return False
        except Exception as e:
            log("class UIController.saver Error\n",traceback.format_exc())
            return False

    def rename(self, default_name, patient_name, num):
        new_name = default_name
        if num in self.rename_list:
            new_id = self.name_list[self.rename_list.index(num)]
            new_name = patient_name + "-" + new_id + "-" + self.current_type
        elif self.current_type == "ScanPost":
            default_name_parts = default_name.split('-')
            default_name_parts[-1] = self.current_type
            new_name = '-'.join(default_name_parts)
        elif self.current_type == "E":
            match = re.search(r'\d+', default_name)
            new_name = patient_name + "-" + str(match.group(0)) + "-" + "Anatomic"
        return new_name

    @staticmethod
    def get_name_list(text):
        tooth_numbers = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r'^(\d+)', line)
            if match:
                tooth_numbers.append(match.group(1))
        return tooth_numbers

    @staticmethod
    def match(handle, bias, imp_path, all_result = False):
        """
        限定范围内
        匹配图案
        """
        try:
            left, top, right, bottom = win32gui.GetWindowRect(handle)
            right_base = left + bias[2]
            if bias[2] == -1:
                right_base = right
            rect = (left + bias[0],
                    top + bias[1],
                    right_base,
                    bottom + bias[3])
            origin_name = win32gui.GetWindowText(handle)
            new_name = re.sub(r'[\\/:*?"<>|]' , "_", origin_name)
            output_name = "screenshot/" + new_name + "-" + str(bias) + ".png"
            results = match_template_in_rect(rect, imp_path, output_name = output_name)
            if len(results) > 0:
                if all_result:
                    result = results
                else:
                    result = results[0]
                return result
            else:
                return False
        except Exception as e:
            log("class UIController.match Error\n",traceback.format_exc())
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
            # key_printer(key)
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
        log("handle_named: no handle named that")
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

        self.current_type = None
        self.current_name = None
        self.current_path = None
        self.hwnd_dict = {
            "handle": [],
            "name": [],
            "snapshot": []
        }
        self.name_list = []
        self.rename_list = []


