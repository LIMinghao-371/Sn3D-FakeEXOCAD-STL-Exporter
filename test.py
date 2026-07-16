import win32gui
from win32con import *

def print_window_tree(hwnd, indent=0, prefix="", is_last=True, max_depth=6, is_first=True):
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
    if len(text) > 30:
        text = text[:27] + "..."

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
    changes = []
    for key in old:
        if old[key] != new[key]:
            print(key, old[key], new[key])
            return key
    return False

