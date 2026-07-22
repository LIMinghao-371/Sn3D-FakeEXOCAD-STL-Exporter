import win32gui
import win32con
import win32api
from PIL import ImageGrab
import time
import os

from win32con import VK_RETURN, VK_SPACE


def wait_for_window_and_save(keyword, save_path=None, timeout=60):
    def is_key_pressed(vk_code):
        # 检查最高有效位（高位为1表示键当前被按下）
        return win32api.GetAsyncKeyState(vk_code) & 0x8000
    """
    循环检测最前方窗口，若标题匹配关键字，则等待用户按空格键保存该窗口截图并退出。

    :param keyword: 窗口标题需要包含的关键字（字符串）
    :param save_path: 截图保存路径（若为 None，则自动生成带时间戳的文件名）
    :param timeout: 最大等待时间（秒），超时返回 False
    :return: True(截图已保存) / False(超时或出错)
    """
    if save_path is None:
        # 自动生成文件名：window_YYYYMMDD_HHMMSS.png
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = f"window_{timestamp}.png"

    print(f"🔍 开始监控前台窗口，目标关键字: '{keyword}'")
    print("⏳ 找到目标窗口后，请按下 空格键 (Space) 截图保存")
    print(f"⏱️ 超时时间: {timeout} 秒")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # 获取当前最前方的窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                time.sleep(0.05)
                continue

            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)

            # 检查是否匹配关键字
            if keyword.lower() in title.lower():
                # 窗口匹配，提示用户
                print(f"\r✅ 已匹配窗口: '{title}'   (按空格截图)", end='')

                # 检查空格键是否被按下
                if is_key_pressed(win32con.VK_DOWN):
                    print("\n✋ 检测到空格按键，正在截图...")

                    # 获取窗口矩形
                    rect = win32gui.GetWindowRect(hwnd)
                    left, top, right, bottom = rect
                    width = right - left
                    height = bottom - top

                    # 防止窗口尺寸异常（极小或负数）
                    if width <= 0 or height <= 0:
                        print("❌ 窗口尺寸异常，无法截图")
                        return False

                    # 截取屏幕对应区域
                    img = ImageGrab.grab(bbox=(left, top, right, bottom))

                    # 保存
                    os.makedirs(os.path.dirname(os.path.abspath(save_path)) or '.', exist_ok=True)
                    img.save(save_path)
                    print(f"✅ 截图已保存至: {save_path}")
                    return True
            else:
                # 没匹配到，显示当前窗口信息（可选）
                # 避免刷屏，每0.5秒打印一次状态
                if int(time.time()) % 1 == 0:
                    print(f"\r🎯 当前窗口: '{title[:30]}...'  等待匹配 '{keyword}'", end='')
        except Exception as e:
            print(f"\n⚠️ 出现错误: {e}")

        time.sleep(0.05)  # 防止CPU满载

    print("\n⏰ 超时，未能在限定时间内完成操作")
    return False
# 例如：检测标题中包含 "保存网格" 的窗口
keyword = "DentalConfig.ExoSearch"
keyword = "exocad DentalCAD 3.3"
if wait_for_window_and_save(keyword, "screenshot/current.png", timeout=30):
    print("截图成功！")
else:
    print("截图失败或超时。")