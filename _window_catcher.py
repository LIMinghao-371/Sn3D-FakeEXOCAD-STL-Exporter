import win32gui
import win32con
import time
from pywinauto import Desktop


#
# def get_edit_text_by_message(edit_hwnd):
#     length = win32gui.SendMessage(edit_hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
#     if length == 0:
#         return ""
#     buffer = win32gui.PyMakeBuffer((length + 1) * 2)
#     win32gui.SendMessage(edit_hwnd, win32con.WM_GETTEXT, length + 1, buffer)
#     return buffer.tobytes().decode('utf-16-le').rstrip('\x00')
#
# def find_edit_recursive(parent_hwnd, depth=0):
#     result = []
#     def enum_cb(child, _):
#         class_name = win32gui.GetClassName(child)
#         if class_name == "Edit":
#             # 尝试用两种方法读取
#             text1 = win32gui.GetWindowText(child)
#             text2 = get_edit_text_by_message(child)
#             print(f"  找到 Edit: HWND={child}")
#             print(f"    GetWindowText: '{text1}'")
#             print(f"    WM_GETTEXT: '{text2}'")
#             result.append((child, text2 if text2 else text1))
#         # 继续递归
#         find_edit_recursive(child, depth+1)
#         return True
#     win32gui.EnumChildWindows(parent_hwnd, enum_cb, None)
#     return result[0] if result else None
#
# def capture_save_dialog_debug(timeout=15):
#     print("⏳ 等待保存对话框...")
#     start = time.time()
#     while time.time() - start < timeout:
#         dlg = win32gui.FindWindow("#32770", None)
#         if dlg:
#             title = win32gui.GetWindowText(dlg)
#             if "保存" in title or "另存" in title or "Save" in title:
#                 print(f"✅ 找到对话框: {title} (HWND: {dlg})")
#                 # 递归查找所有 Edit
#                 edit_info = find_edit_recursive(dlg)
#                 if edit_info:
#                     edit_hwnd, text = edit_info
#                     if text:
#                         print(f"✅ 成功读取文件名: '{text}'")
#                         return dlg, edit_hwnd, text
#                     else:
#                         print("⚠️ Edit 找到了，但内容为空（尝试 UIA 方案）")
#                         # 立即尝试 UIA
#                         uia_text = get_filename_edit_handle(dlg)  # 只试1秒
#                         if uia_text:
#                             print(f"✅ UIA 读到: '{uia_text}'")
#                             return dlg, None, uia_text
#                 else:
#                     print("⏳ 未找到 Edit，继续等待...")
#         time.sleep(0.2)
#     print("❌ 超时")
#     return None, None, None

# def get_filename_edit_handle(dlg):
#     result = [None]
#     def callback(hwnd, _):
#         class_name = win32gui.GetClassName(hwnd)
#         if class_name == "Edit":
#             length = win32gui.SendMessage(hwnd, WM_GETTEXTLENGTH, 0, 0)
#             if length > 0:
#                 buffer = win32gui.PyMakeBuffer((length + 1) * 2)
#                 win32gui.SendMessage(hwnd, WM_GETTEXT, length + 1, buffer)
#                 text = buffer.tobytes().decode('utf-16-le').rstrip('\x00')
#                 if text:
#                     result[0] = text
#                     return False  # 停止枚举
#         return True
#
#     win32gui.EnumChildWindows(dlg, callback, None)
#     if result[0]:
#         print(f"✅ 获取到文件名: '{result[0]}'")
#         return result[0]

if __name__ == "__main__":
    dlg, edit_hwnd, filename = capture_save_dialog_debug()
    if filename:
        print(f"\n最终结果: 文件名 = '{filename}'")
    else:
        print("\n❌ 未能读取文件名，请确认对话框是否打开并已填入默认文件名。")