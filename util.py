import win32gui
from win32con import *
import ctypes
import cv2
import numpy as np
import inspect
from PIL import ImageGrab
import time

def match_template_in_rect(gray, template_path, rect, mode = cv2.IMREAD_GRAYSCALE, threshold=0.9, max_results=10, nms_radius=20):
    """
    在屏幕指定区域内搜索模板图片，返回所有匹配到的位置（非极大值抑制后）

    :param mode:
    :param rect: (left, top, right, bottom) 屏幕绝对坐标
    :param template_path: 模板图片路径
    :param threshold: 匹配度阈值 (0~1)
    :param max_results: 最多返回多少个结果（按匹配度降序）
    :param nms_radius: 非极大值抑制的像素半径（建议设为模板尺寸的一半）
    :return: list of dict，每个 dict 包含：
        'confidence': float,
        'center': (x, y),
        'top_left': (x, y),
        'rect': (l, t, r, b),
        'width': int,
        'height': int
        如果没有匹配，返回空列表。
    """
    # 2. 加载模板
    template = cv2.imread(template_path, mode)
    if template is None:
        return []  # 返回空列表表示加载失败

    h, w = template.shape

    # 3. 模板匹配
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)

    # 4. 获取所有匹配度 >= threshold 的点
    locations = np.where(result >= threshold)
    # locations 是 (y, x) 的两个数组
    points = list(zip(locations[1], locations[0]))  # (x, y) 格式

    if not points:
        return []

    # 5. 非极大值抑制（去掉邻近的重复点）
    #    按匹配度降序排列
    confidences = [result[y, x] for x, y in points]
    sorted_indices = np.argsort(confidences)[::-1]  # 降序

    kept = []
    for idx in sorted_indices:
        x, y = points[idx]
        # 检查该点是否已被抑制（太靠近已保留的点）
        too_close = False
        for kept_x, kept_y in kept:
            if abs(x - kept_x) < nms_radius and abs(y - kept_y) < nms_radius:
                too_close = True
                break
        if not too_close:
            kept.append((x, y))
            if len(kept) >= max_results:
                break

    left, top, right, bottom = rect
    # 6. 构造返回结果
    results = []
    for x, y in kept:
        abs_x = left + x
        abs_y = top + y
        conf = result[y, x]
        results.append({
            'confidence': float(conf),
            'top_left': (abs_x, abs_y),
            'center': (abs_x + w // 2, abs_y + h // 2),
            'rect': (abs_x, abs_y, abs_x + w, abs_y + h),
            'width': w,
            'height': h
        })

    return results

def find_changed_region(img1, img2, threshold=10, min_area=50):
    """
    比较两张PIL图像，找出变化的矩形区域。
    返回:
        rect: (x, y, w, h) 相对于img1左上角的矩形
        region_img: 从img1中裁剪的变化区域图像 (PIL Image)
        diff_img: 差分后的二值图像 (numpy array, 灰度)
    """
    # 转为灰度numpy数组
    gray1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2GRAY)

    # 差分
    diff = cv2.absdiff(gray1, gray2)

    # 二值化
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # 形态学闭运算，连接断裂区域（可选）
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # 查找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, None

    # 假设最大面积的轮廓就是目标变化区域
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < min_area:
        return None, None

    x, y, w, h = cv2.boundingRect(largest)

    # 从img1中裁剪变化区域 (PIL图像)
    region_img = img1.crop((x, y, x + w, y + h))

    return (x, y, w, h), region_img

def print_window_tree(hwnd, indent=0, prefix="", is_last=True, max_depth=6, is_first=True, max_txt = 30):
    """
    递归打印窗口的控件树，高度可读。

    :param hwnd: 要打印的窗口句柄
    :param indent: 当前缩进级别（递归传递）
    :param prefix: 当前行的前缀字符串（用于绘制树状线）
    :param is_last: 当前节点是否是父节点的最后一个子节点
    :param max_depth: 最大递归深度，防止过于深入
    """
    if is_first:
        print(win32gui.IsWindowEnabled(hwnd))
        print(win32gui.GetWindowText(hwnd))
        print(win32gui.GetClassName(hwnd))
    if indent > max_depth:
        return
    print(win32gui.GetWindowRect(hwnd))

    # 获取窗口信息
    try:
        text = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
    except:
        text, cls = "<error>", "<error>"

    # 截断过长的文本（提高可读性）
    if len(text) > max_txt:
        text = text[:max_txt-3] + "..."

    # 构建显示字符串
    # 树状符号：当前节点前的连线
    connector = "└── " if is_last else "├── "
    # 子节点前缀（用于下一层递归）
    child_prefix = prefix + ("    " if is_last else "│   ")

    # 打印当前节点
    print(f"{prefix}{connector}HWND:{hwnd}  Class:{cls}  Text:'{text}'")

    # 递归打印子窗口
    def enum_callback(child_hwnd, extra):
        # 获取子窗口列表（先收集以便判断是否最后一个）
        if not hasattr(extra, 'children'):
            extra.children = []
        extra.children.append(child_hwnd)

    # 第一次遍历收集所有子句柄
    class Data:
        pass

    data = Data()
    data.children = []
    win32gui.EnumChildWindows(hwnd, enum_callback, data)

    children = data.children
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        print_window_tree(child, indent + 1, child_prefix, is_last_child, max_depth, False)


def get_window_snapshot(hwnd):
    """获取某个句柄当前的所有物理状态（用于对比变化）"""
    rect = win32gui.GetWindowRect(hwnd)

    # 基础属性
    return {
        "left": rect[0],
        "top": rect[1],
        "right": rect[2],
        "bottom": rect[3],
        "width": rect[2] - rect[0],
        "height": rect[3] - rect[1],
        "visible": win32gui.IsWindowVisible(hwnd),
        "enabled": win32gui.IsWindowEnabled(hwnd),
        "iconic": win32gui.IsIconic(hwnd),  # 是否最小化
        "text": win32gui.GetWindowText(hwnd),
        # Z序：获取它的上一个兄弟窗口（越上层越靠后）
        "prev_hwnd": win32gui.GetWindow(hwnd, GW_HWNDPREV),
        # 扩展样式（例如 WS_EX_TOPMOST 置顶标志）
        "ex_style": win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    }

def change_snapshots(old, new):
    """简单对比两个快照，输出哪些属性变了"""
    change = False
    for key in old:
        if old[key] != new[key]:
            print(key, ": ", old[key], "->",  new[key])
            change = True
    return change

def get_all_top_hwnds():
    """获取所有可见顶层窗口句柄"""
    hwnds = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True
    win32gui.EnumWindows(callback, None)
    return set(hwnds)


def get_filename_edit_handle(dlg):
    result_text = [None]
    def enum_callback(hwnd, _):
        if win32gui.GetClassName(hwnd) == "Edit":
            print(win32gui.GetWindowText(hwnd))
            length = win32gui.SendMessage(hwnd, WM_GETTEXTLENGTH, 0, 0)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                win32gui.SendMessage(hwnd, WM_GETTEXT, length + 1, buffer)
                text = buffer.value
                if text:  # 非空则认为是文件名
                    result_text[0] = text
                    return False  # 停止枚举
        return True
    win32gui.EnumChildWindows(dlg, enum_callback, None)
    if result_text[0]:
        return result_text[0]
    else:
        return False

def key2str(vk_code):
    """将虚拟键码转换为人类可读的字符串名称（用于可视化/日志）。"""
    mapping = {
        VK_DOWN: "DOWN",
        VK_UP: "UP",
        VK_LEFT: "LEFT",
        VK_RIGHT: "RIGHT",
        VK_RETURN: "ENTER",
        VK_CONTROL: "CTRL",
        VK_SHIFT: "SHIFT",
        VK_MENU: "ALT",
        VK_TAB: "TAB",
        VK_SPACE: "SPACE",
        VK_ESCAPE: "ESC",
        VK_BACK: "BACK",
        VK_DELETE: "DELETE",
        VK_INSERT: "INSERT",
        VK_HOME: "HOME",
        VK_END: "END",
        VK_PRIOR: "PAGE_UP",
        VK_NEXT: "PAGE_DOWN",
        VK_F1: "F1",
    }
    if vk_code in mapping.keys():
        return mapping[vk_code]
    else:
        return chr(vk_code)

def log(*args):
    output = ""
    for arg in args:
        output += " " + str(arg)
    print(output)
    output += "\n"
    return output


import csv
import os

class CSVLogger:
    """
    极简 CSV 日志记录器，支持：
    - 固定列名
    - 动态增加行（add_row）
    - 修改最后一行（update_last）
    - 实时保存（每次操作立即写入文件）
    - 自动创建目录、自动管理表头
    """
    def __init__(self, file_path, columns):
        """
        :param file_path: CSV 文件路径（目录不存在时会自动创建）
        :param columns: 列名列表，第一个列名将作为“行标识”（如文件名）
        """
        self.file_path = file_path
        self.columns = columns
        self.rows = []  # 内存中缓存所有行（字典列表）
        self._ensure_dir()
        self._load_existing()

    def _ensure_dir(self):
        """确保文件所在的目录存在"""
        dir_name = os.path.dirname(self.file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

    def _load_existing(self):
        """如果文件存在且非空，加载已有数据；否则准备空表"""
        if not os.path.isfile(self.file_path):
            return
        if os.path.getsize(self.file_path) == 0:
            return

        with open(self.file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # 检查表头是否与预期一致
            if reader.fieldnames is None:
                return  # 空文件，无表头
            if reader.fieldnames != self.columns:
                raise ValueError(
                    f"现有 CSV 表头 {reader.fieldnames} 与预期 {self.columns} 不一致，无法继续"
                )
            self.rows = list(reader)

    def _save(self):
        """将内存中的所有行覆盖写入 CSV 文件"""
        with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(self.rows)

    def add_row(self, identifier):
        """
        添加新行，第一列填入标识符（如文件名），其余列留空
        """
        row = {col: '' for col in self.columns}
        row[self.columns[0]] = identifier
        self.rows.append(row)
        self._save()

    def update_last(self, column, value):
        """
        修改最后一行的指定列的值，并立即保存
        """
        if not self.rows:
            raise ValueError("还没有任何行，请先调用 add_row() 添加一行")
        if column not in self.columns:
            raise ValueError(f"列 '{column}' 不存在，可用列: {self.columns}")
        self.rows[-1][column] = value
        self._save()

    def get_last_row(self):
        """
        返回最后一行的副本（只读），方便查看当前状态
        """
        if not self.rows:
            return None
        return self.rows[-1].copy()
