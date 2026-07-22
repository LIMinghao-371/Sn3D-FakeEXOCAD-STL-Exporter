# import win32gui
# import win32con
# import win32api
# from PIL import ImageGrab
# import time
# import os
#
# from win32con import VK_RETURN, VK_SPACE
#
#
# def wait_for_window_and_save(keyword, save_path=None, timeout=60):
#     def is_key_pressed(vk_code):
#         # 检查最高有效位（高位为1表示键当前被按下）
#         return win32api.GetAsyncKeyState(vk_code) & 0x8000
#     """
#     循环检测最前方窗口，若标题匹配关键字，则等待用户按空格键保存该窗口截图并退出。
#
#     :param keyword: 窗口标题需要包含的关键字（字符串）
#     :param save_path: 截图保存路径（若为 None，则自动生成带时间戳的文件名）
#     :param timeout: 最大等待时间（秒），超时返回 False
#     :return: True(截图已保存) / False(超时或出错)
#     """
#     if save_path is None:
#         # 自动生成文件名：window_YYYYMMDD_HHMMSS.png
#         timestamp = time.strftime("%Y%m%d_%H%M%S")
#         save_path = f"window_{timestamp}.png"
#
#     print(f"🔍 开始监控前台窗口，目标关键字: '{keyword}'")
#     print("⏳ 找到目标窗口后，请按下 空格键 (Space) 截图保存")
#     print(f"⏱️ 超时时间: {timeout} 秒")
#
#     start_time = time.time()
#
#     while time.time() - start_time < timeout:
#         try:
#             # 获取当前最前方的窗口句柄
#             hwnd = win32gui.GetForegroundWindow()
#             if not hwnd:
#                 time.sleep(0.05)
#                 continue
#
#             # 获取窗口标题
#             title = win32gui.GetWindowText(hwnd)
#
#             # 检查是否匹配关键字
#             if keyword.lower() in title.lower():
#                 # 窗口匹配，提示用户
#                 print(f"\r✅ 已匹配窗口: '{title}'   (按空格截图)", end='')
#
#                 # 检查空格键是否被按下
#                 if is_key_pressed(win32con.VK_DOWN):
#                     print("\n✋ 检测到空格按键，正在截图...")
#
#                     # 获取窗口矩形
#                     rect = win32gui.GetWindowRect(hwnd)
#                     left, top, right, bottom = rect
#                     width = right - left
#                     height = bottom - top
#
#                     # 防止窗口尺寸异常（极小或负数）
#                     if width <= 0 or height <= 0:
#                         print("❌ 窗口尺寸异常，无法截图")
#                         return False
#
#                     # 截取屏幕对应区域
#                     img = ImageGrab.grab(bbox=(left, top, right, bottom))
#
#                     # 保存
#                     os.makedirs(os.path.dirname(os.path.abspath(save_path)) or '.', exist_ok=True)
#                     img.save(save_path)
#                     print(f"✅ 截图已保存至: {save_path}")
#                     return True
#             else:
#                 # 没匹配到，显示当前窗口信息（可选）
#                 # 避免刷屏，每0.5秒打印一次状态
#                 if int(time.time()) % 1 == 0:
#                     print(f"\r🎯 当前窗口: '{title[:30]}...'  等待匹配 '{keyword}'", end='')
#         except Exception as e:
#             print(f"\n⚠️ 出现错误: {e}")
#
#         time.sleep(0.05)  # 防止CPU满载
#
#     print("\n⏰ 超时，未能在限定时间内完成操作")
#     return False
# # 例如：检测标题中包含 "保存网格" 的窗口
# keyword = "DentalConfig.ExoSearch"
# keyword = "exocad DentalCAD 3.3"
# if wait_for_window_and_save(keyword, "screenshot/current.png", timeout=30):
#     print("截图成功！")
# else:
#     print("截图失败或超时。")

import time
import win32gui
import win32con

def close_save_dialog():
    target_class = "#32770"
    target_title_keyword = "另存"
    found = False
    max_attempts = 20   # 最多尝试 20 次（约 10 秒），避免无限循环
    attempt = 0

    while attempt < max_attempts:
        hwnd = win32gui.FindWindow(target_class, None)
        if hwnd:
            title = win32gui.GetWindowText(hwnd)
            if target_title_keyword in title:
                print(f"找到窗口: '{title}' (句柄: {hwnd})")
                found = True
                break
        attempt += 1
        time.sleep(0.5)   # 每 0.5 秒扫描一次

    if not found:
        print("未找到目标窗口")
        return

    # 可选：这里可以调用你的 get_filename_edit_handle(hwnd) 做其他操作
    # result = get_filename_edit_handle(hwnd)

    print("等待 3 秒后关闭窗口...")
    time.sleep(3)

    # 发送 WM_CLOSE 消息（异步，推荐）
    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    # 或者同步：win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    print("已发送关闭消息")

if __name__ == "__main__":
    close_save_dialog()