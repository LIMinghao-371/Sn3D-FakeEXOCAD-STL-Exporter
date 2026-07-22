import cv2
from PIL import ImageGrab, ImageDraw

from util import *
import win32api
import pyperclip
import time
import traceback
import re
import os

class UIController:
    def __init__(self, dlg):
        # 主窗口句柄，要复用，不能清除
        self.dlg = dlg
        self.main_handle = dlg.handle
        # 可以清除
        self.current_type = None
        self.current_name = None
        self.current_path = None
        self.current_success = None
        self.current_failed = None
        self.current_invalid = None
        self.show_hide_handle = None
        self.guide_bar_handle = None
        self.current_index = 0
        self.current_rename = 0
        self.current_tasks = [{}]
        self.current_hole_fill_tasks = []
        self.current_name_list = []
        self.log_dict = {
            "success": 0,
            "failed": 0,
            "invalid": 0,
        }
        # 只读，无须清除
        self.black_dict = {}

        self.search_menu_clue = "DentalConfig.ExoSearch"
        self.main_window_clue = "exocad DentalCAD 3.3"

        self.judge_pale_mean = 245
        self.judge_pale_std = 1.0
        self.judge_pale_w = 25
        self.judge_pale_h = 50
        self.judge_menu_t = 4
        self.judge_menu_h = 500

        self.load_timeout = 60.0  # 数据加载
        self.clear_timeout = 30.0  # 项目删除
        self.merge_timeout = 30.0
        self.delete_timeout = 5.0
        self.pop_timeout = 5.0 # 窗口更新,考虑到后续卡顿，统一设为5秒
        self.cam_refresh_timeout = 3.0
        self.menu_timeout = 2.0
        self.ui_timeout = 0.5 # 检测覆盖文件提示

        self.wait_menu_switch = 1.0
        self.wait_ui_done = 0.5  # UI更新
        self.wait_save_disappear = 0.25
        self.wait_copy_txt = 0.25
        self.wait_click = 0.1  # 点击延迟
        self.wait_down = 0.05  # 按键延迟

        self.render_max = 3 # 检测功能菜单弹窗最多次数，用以判断单数据或多数据
        self.load_render_max = 3 # 检测功能菜单弹窗最多次数，用以判断单数据或多数据

        self.close_bias = (0, -10)
        self.hide_all_bias = (-120, -20)
        self.eye_click_bias = (40, 0)
        self.eye_bar_bias = (25, 20, 550, -20)
        self.search_bar_bias = (0, 0, 60, 0)
        self.full_bias = (0, 0, -1, 0)

        self.window_dict = {
            "eye": "icon/window/eye.png",
            "load": "icon/window/load.png",
            "loaded": "icon/window/loaded.png",
            "guide": "icon/window/guide.png",
            "guide_bar_done": "icon/window/guide_bar_done.png",
            "advanced": "icon/window/advanced.png",
            "show_hide": "icon/window/show_hide.png",
            "hole_fill_delete": "icon/window/hole_fill_delete.png",
            "hole_fill_delete_confirm": "icon/window/hole_fill_delete_confirm.png",
            "hole_fill_merge": "icon/window/hole_fill_merge.png",
            "hole_fill_merge_done": "icon/window/hole_fill_merge_done.png",
            "hole_fill_merge_select": "icon/window/hole_fill_merge_select.png",
            "hole_fill_merge_selected": "icon/window/hole_fill_merge_selected.png",
            "hole_fill_merge_confirm": "icon/window/hole_fill_merge_confirm.png",
            "menu_switch": "icon/window/menu_switch.png",
            "menu_function": "icon/window/menu_function.png",
            "menu_database": "icon/window/menu_database.png",
            "menu_delete": "icon/window/menu_delete.png",
            "menu_merge": "icon/window/menu_merge.png",
            "menu_close": "icon/window/menu_close.png",
            "search_bar": "icon/window/search_bar.png",
            "save": "icon/window/save.png",
            "close": "icon/window/close.png",
            "closed": "icon/window/closed.png",
        }
        self.group_dict = {
            "Antagonist": "icon/group/Antagonist.png",
            "Scans": "icon/group/Scans.png",
            "ScanPost": "icon/group/ScanPost.png",
            "Gingiva": "icon/group/Gingiva.png",
            "Anatomic": "icon/group/Anatomic.png",
            "Merged": "icon/group/Merged.png",
        }
        self.white_dict = {
            "to_choose": {
                "Antagonist": False,
                "Scans": "icon/white/to_choose/Scans.png",
                "ScanPost": "icon/white/to_choose/ScanPost.png",
                "Gingiva": "icon/white/to_choose/Gingiva.png",
                "Anatomic": False,
                "Merged": False,
                "None": "icon/white/to_choose/None.png",
            },
            "to_rename": {
                "Antagonist": False,
                "Scans": False,
                "ScanPost": {
                    "path": "icon/white/to_rename/ScanPost.png",
                    "keyword": "ScanPost",
                },
                "Gingiva": False,
                "Anatomic": {
                    "keyword": "Anatomic"
                },
                "Merged": False,
            },
        }
        self.database_dict = {
            "数据库模型信息": "牙形数据库",
            "植体替代体配置信息": "种植体数据库",
        }

    def process(self, current_path, current_name):
        """
        跑一遍流程
        """
        self.variable_init()
        self.dir_init(current_path, current_name)
        self.delete_if_need()
        if not self.load():
            return False
        if not self.judge("Merged"):
            return False
        self.to_save("Antagonist")
        self.to_save("Scans")
        self.to_save("ScanPost", name_from_database="数据库模型信息")
        self.to_save("Gingiva")
        self.to_save("Anatomic", name_from_database="数据库模型信息")
        if self.to_save("Merged"):
            self.to_fill_hole()
        return True

    def delete_if_need(self):
        handle = win32gui.GetForegroundWindow()
        close_icon = self.match(handle,self.full_bias,self.window_dict["close"])
        if close_icon:
            self.keyboard(handle, VK_RETURN)
            if self.wait_component(self.main_handle, self.clear_timeout, self.window_dict["closed"]):
                # 当真的出现这个情况时，不管怎么样，都会连累后续数据。区别只是连累一个还是全部
                return True
            else:
                log_txt = log("项目删除超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        else:
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
            rect = win32gui.GetWindowRect(self.main_handle)
            pos = (int((rect[0] + rect[2])/2), int((rect[0] + rect[2])/2))
            self.click(self.main_handle, pos)
            pyperclip.copy(self.current_path) # 复制到剪切板
            self.keyboard(self.main_handle,
                          VK_CONTROL, ord("V")) # Ctrl+ V 粘贴
            pop_hwnd = self.wait_window(self.main_handle,self.pop_timeout,self.window_dict["load"])
            self.keyboard(pop_hwnd,
                          VK_RETURN) # Enter 确认
            time.sleep(self.wait_copy_txt) # 由于 EXO CAD 异步事件特性，需要在这里等待事件处理完毕，否则引起意想不到的bug
            self.show_hide_handle = self.wait_window(self.main_handle, self.load_timeout, self.window_dict["show_hide"])
            if self.show_hide_handle:
                if self.wait_component(self.main_handle,self.pop_timeout,self.window_dict["loaded"]):
                    self.guide_bar_handle = self.wait_window(self.main_handle, self.cam_refresh_timeout,self.window_dict["guide_bar_done"])
                    if self.guide_bar_handle:
                        log_txt = log("加载成功")
                        log_type = "success"
                        self.log_txt_output(log_type, log_txt)
                        return True
                    else:
                        log_txt = log("向导未结束")
                        log_type = "invalid"
                        self.log_txt_output(log_type, log_txt)
                        return False
                else:
                    log_txt = log("等待UI更新超时")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    return False
            else:
                log_txt = log("找不到 显示/隐藏 窗口句柄")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def hide_all(self):
        """
        点击左上角收起 显示/隐藏 面板 (测试一下)
        Ctrl + 点击 隐藏全部
        点击右上角展开 显示/隐藏 面板 (测试一下)
        """
        try:
            show_hide_handle = self.show_hide_handle
            root_handle = win32gui.GetForegroundWindow()
            left, top, right, bottom = win32gui.GetWindowRect(show_hide_handle)
            self.click(root_handle,
                       (right + self.hide_all_bias[0],
                        bottom + self.hide_all_bias[1]),
                       True,
                       wait=self.wait_ui_done)
            start = time.time()
            while time.time() - start < self.pop_timeout:
                if not self.match(show_hide_handle,
                                  self.eye_bar_bias,
                                  self.window_dict["eye"]):
                    break
            log_txt = log("全体隐藏显示 成功")
            log_type = "success"
            self.log_txt_output(log_type, log_txt)
            return True
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def judge(self, group, false_mode = True):
        """
        检测是否有 某个数据？
        点击 键盘对应按键
        如果对应小眼睛亮了，说明有
        """
        try:
            show_hide_handle = self.show_hide_handle
            rect = win32gui.GetWindowRect(self.main_handle)
            pos = (int((rect[0] + rect[2]) / 2), int((rect[0] + rect[2]) / 2))
            win32api.SetCursorPos(pos)
            result = self.match(show_hide_handle,
                                    self.full_bias,
                                    self.group_dict[group])
            if result:
                log_txt = log("数据合法")
                log_type = "success"
                self.log_txt_output(log_type, log_txt)
                self.log_imp_output(log_type, self.show_hide_handle)  # 依靠他创建
                return True
            elif not false_mode:
                return False
            else:
                log_txt = log(": 缺乏 合并部分 的数据")
                log_type = "invalid"
                self.log_txt_output(log_type, log_txt)
                self.log_imp_output(log_type, self.show_hide_handle)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def to_save(self, group, name_from_database = None, wait = None):
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
            self.current_name_list = []
            show_hide_handle = self.show_hide_handle
            rect = win32gui.GetWindowRect(self.main_handle)
            pos = (int((rect[0] + rect[2]) / 2), int((rect[0] + rect[2]) / 2))
            win32api.SetCursorPos(pos)
            eye_result = self.match(show_hide_handle,
                                        self.full_bias,
                                        self.group_dict[group],)
            if len(self.current_hole_fill_tasks) == 0:
                self.current_type = group
            else:
                self.current_type = "HoleFill"
            self.current_tasks = [{}]
            self.current_index = 0
            self.current_rename = 0
            assume_one_task = True
            if type(eye_result) == dict:
                log_txt = log("检测到数据:", self.current_type)
                log_type = "success"
                self.log_txt_output(log_type, log_txt)
                eye_pos = eye_result["center"]
                if name_from_database is not None:
                    menu_handle = self.search_menu(show_hide_handle,eye_pos,name_from_database,self.window_dict["menu_database"])
                    if menu_handle:
                        self.keyboard(menu_handle,
                                      VK_RETURN)
                        database_handle = self.wait_window(menu_handle,self.ui_timeout,self.database_dict[name_from_database],txt_mode=True)
                        if database_handle:
                            self.keyboard(database_handle,
                                          VK_CONTROL, ord("C"))
                            time.sleep(self.wait_copy_txt)
                            self.current_name_list = self.get_name_list(pyperclip.paste())
                            self.keyboard(database_handle,
                                          VK_RETURN)
                        else:
                            self.keyboard(menu_handle,
                                          VK_ESCAPE)
                            log("there is no ", name_from_database)
                        time.sleep(self.wait_ui_done) # 防止事件堵塞队列，防止消息队列积压与UI线程饥饿
                if len(self.current_hole_fill_tasks) > 0:
                    self.current_tasks = self.current_hole_fill_tasks
                    assume_one_task = False
                while self.current_index < len(self.current_tasks):
                    menu_handle = self.search_menu(self.show_hide_handle, eye_pos, "功能菜单", self.window_dict["menu_function"],wait=wait)
                    if menu_handle:
                        target_hwnd, search_result = self.check_new_pop(menu_handle) # 点击，检测新窗口
                        if target_hwnd is None or search_result is None:
                            log_txt = log("找不到 工具菜单 的 新窗口 或 匹配失败")
                            log_type = "failed"
                            self.log_txt_output(log_type, log_txt)
                            return False
                        else:
                            root_rect = win32gui.GetWindowRect(target_hwnd)
                            if assume_one_task or len(self.current_hole_fill_tasks) == 1:
                                if search_result is not False: # 单个数据
                                    task_dict = {"pos": search_result["center"]}
                                    if len(self.current_name_list) > 0:
                                        task_dict["id"] = self.current_name_list[0]
                                    self.current_tasks = [task_dict]
                                    self.selector(target_hwnd, search_result["center"])
                                else: # 多个数据
                                    assume_one_task = False
                                    self.current_tasks = self.get_task(target_hwnd, group)
                                    if len(self.current_tasks) > 0:
                                        delta_pos = self.current_tasks[self.current_index]["pos"]
                                        pos = (root_rect[0]+delta_pos[0],root_rect[1]+delta_pos[1])
                                        self.selector(target_hwnd, pos, multi_task = True)
                                    else:
                                        log_txt = log("找不到 匹配的保存任务")
                                        log_type = "failed"
                                        self.log_txt_output(log_type, log_txt)
                                        self.log_imp_output(log_type, target_hwnd)
                                        return False
                            elif len(self.current_tasks) > 0:
                                delta_pos = self.current_tasks[self.current_index]["pos"]
                                pos = (root_rect[0]+delta_pos[0],root_rect[1]+delta_pos[1])
                                self.selector(target_hwnd, pos, multi_task=True)
                            self.current_index += 1
                    else:
                        log_txt = log("唤起右键窗口失败")
                        log_type = "failed"
                        self.log_txt_output(log_type, log_txt)
                        return False
                if self.current_index == 0:
                    log_txt = log("没有任何数据被保存")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    return False
                else:
                    return True
            else:
                log_txt = log("根本没有这种数据:", self.current_type)
                log_type = "invalid"
                self.log_txt_output(log_type, log_txt)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def to_fill_hole(self):
        if len(self.current_hole_fill_tasks) == 0:
            log_txt = log("无需修复")
            log_type = "invalid"
            self.log_txt_output(log_type, log_txt)
            return False
        else:
            advanced = self.wait_component(self.main_handle, self.pop_timeout, self.window_dict["advanced"])
            if advanced:
                self.click(self.main_handle, advanced["center"],wait=self.wait_ui_done)
                if self.wait_component(self.main_handle, self.pop_timeout, self.window_dict["guide"]):
                    if self.hole_fill_delete():
                        if self.hole_fill_merge():
                            guide = self.wait_component(self.main_handle,self.pop_timeout,self.window_dict["guide"])
                            if guide:
                                self.click(self.main_handle,guide["center"],wait=self.wait_ui_done)
                                if self.wait_component(self.main_handle, self.pop_timeout, self.window_dict["advanced"]):
                                    time.sleep(self.wait_copy_txt)
                                    self.to_save("Merged",wait=self.wait_click)
                                    return True
                                else:
                                    log_txt = log("等待向导超时")
                                    log_type = "failed"
                                    self.log_txt_output(log_type, log_txt)
                                    return False
                            else:
                                log_txt = log("返回向导失败")
                                log_type = "failed"
                                self.log_txt_output(log_type, log_txt)
                                return False
                        else:
                            log_txt = log("合并并保存修复体 出错")
                            log_type = "failed"
                            self.log_txt_output(log_type, log_txt)
                            return False
                    else:
                        log_txt = log("删除修复体 出错")
                        log_type = "failed"
                        self.log_txt_output(log_type, log_txt)
                        return False
                else:
                    log_txt = log("等待高阶模式超时")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    return False
            else:
                log_txt = log("打开高阶模式失败")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False

    def hole_fill_delete(self):
        root_handle = win32gui.GetForegroundWindow()
        menu_handle = self.search_menu(root_handle, None, "删除构建的部分",
                                       self.window_dict["menu_delete"], q_mode=True)
        if menu_handle:
            self.keyboard(menu_handle,
                          VK_RETURN)
            delete_window = self.wait_window(menu_handle, self.pop_timeout,
                                             self.window_dict["hole_fill_delete"])
            if delete_window:
                confirm_button = self.wait_component(delete_window, self.pop_timeout, self.window_dict["hole_fill_delete_confirm"])
                if confirm_button:
                    self.click(delete_window, confirm_button["center"],wait=self.wait_click)
                    if self.wait_disappear(delete_window,self.pop_timeout):
                        return True
                    else:
                        log_txt = log("确定按钮响应超时")
                        log_type = "failed"
                        self.log_txt_output(log_type, log_txt)
                        return False
                else:
                    log_txt = log("寻找确定按钮超时")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    return False
            else:
                log_txt = log("等待 删除修复体 弹窗超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        else:
            log_txt = log("唤起二次搜索菜单失败")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def hole_fill_merge(self):
        root_handle = win32gui.GetForegroundWindow()
        menu_handle = self.search_menu(root_handle, None, "合并并保存修复体",
                                       self.window_dict["menu_merge"], q_mode=True)
        if menu_handle:
            self.keyboard(menu_handle,
                          VK_RETURN)
            merge_window = self.wait_window(menu_handle, self.pop_timeout,self.window_dict["hole_fill_merge"])
            if merge_window:
                selected = self.wait_component(merge_window,self.ui_timeout,self.window_dict["hole_fill_merge_selected"],false_mode=False)
                if not selected:
                    select = self.wait_component(merge_window,self.pop_timeout,self.window_dict["hole_fill_merge_select"])
                    if select:
                        self.click(merge_window, select["center"], wait=self.wait_click)
                        if not self.wait_component(merge_window,self.ui_timeout,self.window_dict["hole_fill_merge_selected"]):
                            log_txt = log("选择框反应超时")
                            log_type = "failed"
                            self.log_txt_output(log_type, log_txt)
                            return False
                    else:
                        log_txt = log("寻找选择框超时")
                        log_type = "failed"
                        self.log_txt_output(log_type, log_txt)
                        return False
                if self.wait_window(root_handle,self.merge_timeout,self.window_dict["hole_fill_merge_done"]):
                    confirm_button = self.wait_component(merge_window,self.pop_timeout,self.window_dict["hole_fill_merge_confirm"])
                    if confirm_button:
                        self.click(merge_window, confirm_button["center"], wait=self.wait_click)
                        if self.wait_disappear(merge_window, self.pop_timeout):
                            return True
                        else:
                            log_txt = log("确定按钮响应超时")
                            log_type = "failed"
                            self.log_txt_output(log_type, log_txt)
                            return False
                    else:
                        log_txt = log("寻找确认按钮 超时")
                        log_type = "failed"
                        self.log_txt_output(log_type, log_txt)
                        return False
                else:
                    log_txt = log("合并并保存修复体 超时")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    return False
            else:
                log_txt = log("等待 合并并保存修复体 弹窗超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        else:
            log_txt = log("唤起搜索菜单失败")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def search_menu(self, handle, pos, txt, imp_path, q_mode=False, wait=None):
        if not q_mode:
            menu_handle = self.call_right_menu(handle, pos, wait=wait)  # 右键，唤起右键菜单
        else:
            menu_handle = self.call_search_menu(handle, wait=wait)  # 右键，唤起右键菜单
        if menu_handle:
            pyperclip.copy(txt)  # 搜索功能菜单
            time.sleep(self.wait_copy_txt)
            self.keyboard(menu_handle,
                          VK_CONTROL, ord("V"))
            time.sleep(1)
            if self.wait_window(handle, self.menu_timeout, imp_path, mode=cv2.TM_SQDIFF):
                return menu_handle
            else:
                log_txt = log("搜索栏超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                self.log_imp_output(log_type, menu_handle)
        elif not q_mode:
            log_txt = log("右键菜单窗口 响应超时")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            self.log_imp_output(log_type, menu_handle)
        else:
            log_txt = log("Ctrl+Q窗口 响应超时")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            self.log_imp_output(log_type, menu_handle)
        return False

    def call_search_menu(self, handle, wait=None):
        try:
            root_handle = win32gui.GetForegroundWindow()
            self.keyboard(handle,
                          VK_CONTROL, ord("Q"))
            menu_handle = self.wait_window(root_handle, self.pop_timeout, self.window_dict["search_bar"])
            if menu_handle:
                return menu_handle
            else:
                log_txt = log("Ctrl+Q弹窗等待超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def call_right_menu(self, handle, pos, wait=None):
        try:
            root_handle = win32gui.GetForegroundWindow()
            self.click(handle,
                       (pos[0] + self.eye_click_bias[0],
                        pos[1] + self.eye_click_bias[1]), button="right", back=False, wait=wait)
            menu_handle = self.wait_window(root_handle, self.pop_timeout, self.window_dict["search_bar"])
            if menu_handle:
                return menu_handle
            else:
                log_txt = log("右键弹窗等待超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def check_new_pop(self, handle):
        target_hwnd = None
        search_result = None
        before = get_all_top_hwnds()
        self.keyboard(handle,
                      VK_RETURN)
        render_time = 0
        start = time.time()
        break_all = False
        while time.time() - start < self.pop_timeout and not break_all:
            after = get_all_top_hwnds()
            new_handles = after - before
            for hwnd in new_handles:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                title = win32gui.GetWindowText(hwnd)
                if width > 100 and height > 50 and title == "":  # 很怪 但是这个判断方式确实不错
                    render_time += 1
                    target_hwnd = hwnd
                    search_result = self.match(hwnd, self.search_bar_bias, self.window_dict["save"])
                    if search_result or render_time >= self.render_max:
                        break_all = True
                        break
        return target_hwnd, search_result

    def get_task(self, target_hwnd, group):
        try:
            white_keyname = self.white_dict["to_choose"][group]
            rename_dict = self.white_dict["to_rename"][group]
            rect = win32gui.GetWindowRect(target_hwnd)
            new_menu = ImageGrab.grab(bbox=rect)
            time.sleep(self.wait_down)
            first_selection_imp = None
            start = time.time()
            select_num = 0
            task_list = []
            while time.time() - start < self.pop_timeout:
                self.keyboard(target_hwnd, VK_DOWN)
                time.sleep(self.wait_down)
                current_menu = ImageGrab.grab(bbox=rect)
                selected_delta_rect, selected_imp = find_changed_region(new_menu, current_menu)
                if selected_imp is not None:
                    root_imp = cv2.cvtColor(np.array(selected_imp), cv2.COLOR_BGR2GRAY)
                    if first_selection_imp is None:
                        first_selection_imp = selected_imp
                    elif np.array_equal(np.array(first_selection_imp),np.array(selected_imp)):
                        return task_list
                    abs_rect = (rect[0] - selected_delta_rect[0],
                                rect[1] - selected_delta_rect[1],
                                rect[2] - selected_delta_rect[2],
                                rect[3] - selected_delta_rect[3])
                    task_dict = None
                    none_imp = root_imp[0:self.judge_pale_h, 0:self.judge_pale_w]
                    # cv2.imwrite("screenshot/none" + str(select_num) + ".png", none_imp)
                    if np.mean(none_imp) > self.judge_pale_mean and np.std(none_imp) < self.judge_pale_std:
                        if not white_keyname:
                            task_pos = (20, selected_delta_rect[1] + 20)
                            task_dict = {"pos": task_pos}
                        elif self.match(None, None, white_keyname ,root_imp = root_imp, rect = abs_rect):
                            task_pos = (20, selected_delta_rect[1] + 20)
                            task_dict = {"pos": task_pos}
                        if task_dict is not None:
                            if rename_dict and len(self.current_name_list) > 0:
                                if "path" in rename_dict and self.match(None, None, rename_dict["path"] ,root_imp = root_imp, rect = abs_rect):
                                    task_dict["id"] = self.current_name_list[self.current_rename]
                                    self.current_rename += 1
                                elif "path" not in rename_dict:
                                    task_dict["id"] = self.current_name_list[self.current_rename]
                                    self.current_rename += 1
                            task_list.append(task_dict)
                        # if task_dict is not None:
                            # cv2.imwrite("screenshot/selected" + str(select_num) + ".png", root_imp)
                        # else:
                            # cv2.imwrite("screenshot/rejected" + str(select_num) + ".png", root_imp)
                        select_num += 1
                else:
                    log_txt = log("未检测到下箭头的选中事件")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    self.log_imp_output(log_type, target_hwnd)
                    return False
            log_txt = log("数据列表搜索时间超时")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            self.log_imp_output(log_type, target_hwnd)
            return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

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

    def selector(self, hwnd, pos, multi_task = False):
        try:
            self.click(hwnd, pos)
            if multi_task:
                for i in range(3):
                    self.keyboard(hwnd, VK_DOWN)
                self.keyboard(hwnd, VK_RETURN)
            self.saver()
            return True
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def saver(self):
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
                            break
            if save_handle is not None:
                new_name = self.rename(default_name)
                pyperclip.copy(new_name)
                time.sleep(self.wait_copy_txt)
                self.keyboard(save_handle,
                              VK_CONTROL, ord("V"))
                self.keyboard(save_handle,
                              VK_RETURN)
                output_message = ": 已保存"
                start = time.time()
                while time.time() - start < self.ui_timeout:
                    hwnd = win32gui.FindWindow("#32770", None)
                    title = win32gui.GetWindowText(hwnd)
                    if "确认另存为" in title:
                        time.sleep(self.wait_click)
                        self.keyboard(save_handle,
                                      VK_LEFT, activate=False)
                        self.keyboard(save_handle,
                                      VK_RETURN, activate=False)
                        output_message = ": 已覆盖"
                        break
                start = time.time()
                while time.time() - start < self.pop_timeout:
                    hwnd = win32gui.FindWindow("#32770", None)
                    if not hwnd or not "保存" in win32gui.GetWindowText(hwnd):
                        time.sleep(self.wait_save_disappear)
                        current_handle = win32gui.GetForegroundWindow()
                        if win32gui.GetWindowText(current_handle) == "":
                            self.keyboard(current_handle,
                                          VK_RETURN, activate=False) # 如果跳出询问弹窗
                            self.wait_window(current_handle,self.pop_timeout,self.main_window_clue,txt_mode=True)
                        break
                log_txt = log("保存成功: \n", new_name, output_message)
                log_type = "success"
                self.log_txt_output(log_type, log_txt)
                return True
            else:
                log_txt = log("未检测到 保存 窗口句柄")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def rename(self, default_name):
        new_name = default_name
        patient_name = self.current_name
        task = self.current_tasks[self.current_index]
        if self.current_type == "ScanPost" and len(self.current_name_list) > 0:
            if "id" in task.keys():
                new_name = patient_name + "-" + task["id"] + "-" + self.current_type
            else:
                default_name_parts = default_name.split('-')
                default_name_parts[-1] = self.current_type
                new_name = '-'.join(default_name_parts)
        elif self.current_type == "Anatomic":
            if "id" in task.keys():
                new_name = patient_name + "-" + task["id"] + "-" + self.current_type
            else:
                match = re.search(r"牙齿_([^_]+)", default_name)
                if match:
                    new_name = patient_name + "-" + match.group(1) + "-" + self.current_type
        elif self.current_type == "Merged" or self.current_type == "HoleFill":
            default_name_part = default_name.split("-")
            default_type = default_name_part[-1].split(".")[0]
            default_type = default_type.split('_')[0]
            default_type = default_type.capitalize()
            default_id = default_name_part[-2]
            if self.current_type == "HoleFill":
                default_type += "-" + self.current_type
            elif "Abutment" not in default_type and task:
                self.current_hole_fill_tasks.append(task)
            new_name = patient_name + "-" + default_id + "-" + default_type
        success_path = self.get_save_path("success")
        output_name = success_path + self.current_name + "\\" + new_name
        print(output_name)
        return output_name

    def get_save_path(self, log_type):
        if log_type == "success":
            chosen_path = self.current_success
        elif log_type == "failed":
            chosen_path = self.current_failed
        elif log_type == "invalid":
            chosen_path = self.current_invalid
        else:
            print("log_type: " ,log_type)
            return None
        return chosen_path

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
    def match(handle, bias, imp_path, all_result = False, root_imp = None, rect = None, mode = cv2.IMREAD_GRAYSCALE):
        """
        限定范围内
        匹配图案
        """
        try:
            if root_imp is None:
                left, top, right, bottom = win32gui.GetWindowRect(handle)
                right_base = left + bias[2]
                if bias[2] == -1:
                    right_base = right
                rect = (left + bias[0],
                        top + bias[1],
                        right_base,
                        bottom + bias[3])
                screenshot = ImageGrab.grab(bbox=rect)
                img_np = np.array(screenshot)
                root_imp = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

                output_name = "screenshot/" + "-" + str(bias) + ".png"
                cv2.imwrite(output_name, root_imp)

            results = match_template_in_rect(root_imp, imp_path, rect, mode = mode)
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

    def wait_window(self, root_handle, timeout, clue, txt_mode = False, bias = None, strict = False, mode = cv2.IMREAD_GRAYSCALE):
        try:
            if bias is None:
                bias = self.full_bias
            start = time.time()
            while time.time() - start < timeout:
                current_handle = win32gui.GetForegroundWindow()
                if current_handle != root_handle and current_handle != 0:
                    if txt_mode is False and self.match(current_handle, bias, clue, mode=mode):
                        return current_handle
                    elif txt_mode is True:
                        if not strict and clue in win32gui.GetWindowText(current_handle):
                            return current_handle
                        elif strict and clue == win32gui.GetWindowText(current_handle):
                            return current_handle
            log_txt = log("窗口检测超时")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            self.log_imp_output(log_type, root_handle)
            return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def wait_disappear(self, handle, timeout):
        try:
            start = time.time()
            while time.time() - start < timeout:
                if not win32gui.IsWindow(handle):
                    return True
            log_txt = log("等待窗口消失超时")
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            self.log_imp_output(log_type, handle)
            return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def wait_component(self, handle, timeout, clue, false_mode = True):
        try:
            start = time.time()
            while time.time() - start < timeout:
                result = self.match(handle, self.full_bias, clue)
                if result:
                    return result
            if false_mode:
                log_txt = log("组件检测超时")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                self.log_imp_output(log_type, handle)
            return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
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
            key_printer(key)
        for key in reversed(keys):
            win32api.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)

    def click(self, handle, pos, ctrl = False, button = "left", back = True, wait = None):
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

        # left, top, right, bottom = win32gui.GetWindowRect(handle)
        # img = ImageGrab.grab(bbox=(left, top, right, bottom))
        # gray_img = img.convert('L')
        # rel_x = pos[0] - left
        # rel_y = pos[1] - top
        # rgb_img = gray_img.convert('RGB')
        # draw = ImageDraw.Draw(rgb_img)
        # radius = 10
        # if button == "left":
        #     color = "red"
        # else:
        #     color = "blue"
        # draw.ellipse((rel_x - radius, rel_y - radius, rel_x + radius, rel_y + radius),
        #              fill=color)
        # rgb_img.save("screenshot\\" + str(time.time()) + ".png")

        if wait is not None:
            time.sleep(wait)
        if ctrl:
            win32api.keybd_event(VK_CONTROL, 0, 0, 0)
        win32api.mouse_event(down_event, 0, 0, 0, 0)
        win32api.mouse_event(up_event, 0, 0, 0, 0)
        if ctrl:
            win32api.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        if back:
            win32api.SetCursorPos(old_pos)

    def dir_init(self, current_path, current_name):
        try:
            self.current_path = current_path
            self.current_name = current_name
            parent_path = os.path.dirname(os.path.dirname(current_path))
            self.current_success = parent_path + "-success\\"
            self.current_failed = parent_path + "-failed\\"
            self.current_invalid = parent_path + "-invalid\\"
            if not os.path.exists(self.current_success):
                os.mkdir(self.current_success)
            if not os.path.exists(self.current_failed):
                os.mkdir(self.current_failed)
            if not os.path.exists(self.current_invalid):
                os.mkdir(self.current_invalid)
            time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            success_log_path = self.current_success + "success-log.txt"
            failed_log_path = self.current_failed + "failed-log.txt"
            invalid_log_path = self.current_invalid + "invalid-log.txt"
            if not os.path.exists(success_log_path):
                with open(self.current_success + "success-log.txt", 'w') as f:
                    f.write(time_str)
            if not os.path.exists(failed_log_path):
                with open(self.current_failed + "failed-log.txt", 'w') as f:
                    f.write(time_str)
            if not os.path.exists(invalid_log_path):
                with open(self.current_invalid + "invalid-log.txt", 'w') as f:
                    f.write(time_str)
            return True
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

    def variable_init(self):
        self.current_type = None
        self.current_name = None
        self.current_path = None
        self.current_success = None
        self.current_failed = None
        self.current_invalid = None
        self.show_hide_handle = None
        self.guide_bar_handle = None
        self.current_index = 0
        self.current_rename = 0
        self.current_tasks = [{}]
        self.current_hole_fill_tasks = []
        self.current_name_list = []
        self.log_dict = {
            "success": 0,
            "failed": 0,
            "invalid": 0,
        }

    def log_txt_output(self, log_type, log_txt):
        path = self.get_save_path(log_type) + log_type + "-log.txt"
        if log_type == "invalid" or log_type == "failed":
            log_txt = self.current_name + ": " + str(self.log_dict[log_type]) + ": " + log_txt
            print(log_txt)
        with open(path, "a") as f:
            f.write(log_txt)

    def log_imp_output(self, log_type, handle):
        path = self.get_save_path(log_type) + self.current_name + "\\"
        if not os.path.exists(path):
            os.mkdir(path)
        rect = win32gui.GetWindowRect(handle)
        imp = ImageGrab.grab(bbox=rect)
        imp.save(path + log_type + "-log-" + str(self.log_dict[log_type]) + ".png")
        self.log_dict[log_type] += 1

    def clear(self):
        try:
            print("clear")
            current_root_handle = win32gui.GetForegroundWindow()
            menu_handle = self.search_menu(current_root_handle,None,"关闭项目文件",self.window_dict["menu_close"],q_mode=True)
            if menu_handle:
                self.keyboard(menu_handle,VK_RETURN)
                time.sleep(self.wait_ui_done) # 释放事件，防止UI饿死
                close_handle = self.wait_window(current_root_handle,self.pop_timeout,self.window_dict["close"])
                if close_handle:
                    self.keyboard(close_handle, VK_RETURN)
                    if self.wait_component(self.main_handle,self.clear_timeout,self.window_dict["closed"]):
                        return True
                    else:
                        log_txt = log("项目删除超时")
                        log_type = "failed"
                        self.log_txt_output(log_type, log_txt)
                        return False
                else:
                    log_txt = log("未检测到退出弹窗")
                    log_type = "failed"
                    self.log_txt_output(log_type, log_txt)
                    return False
            else:
                log_txt = log("未检测到右键菜单")
                log_type = "failed"
                self.log_txt_output(log_type, log_txt)
                return False
        except Exception as e:
            log_txt = log("error: ", traceback.format_exc())
            log_type = "failed"
            self.log_txt_output(log_type, log_txt)
            return False

