import io
import os
import subprocess
import sys
import time
import cv2
import numpy as np
import psutil
from PIL import Image
import requests
def is_connected_http(timeout=5, retry=2):
    """
    通过HTTP请求检测网络（验证能否正常访问互联网）
    :param timeout: 单次请求超时时间（秒）
    :param retry: 重试次数
    :return: True（有网且可访问）/False（无网或不可访问）
    """
    # 测试URL：返回简单响应的公共接口（无内容限制）
    test_urls = [
        "https://www.baidu.com",  # 百度首页
        "https://www.taobao.com"  # 淘宝（国内稳定）
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
    }  # 设置请求头，避免部分服务器拒绝无UA的请求

    for _ in range(retry):
        for url in test_urls:
            try:
                # 发送HEAD请求（比GET更轻量，仅获取响应头）
                response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
                # 状态码2xx/3xx视为成功（3xx是重定向，通常表示服务器可达）
                if response.status_code in range(200, 400):
                    return True
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException):
                # 请求超时/连接错误/其他请求异常，尝试下一个URL
                continue
        time.sleep(1)
    return False


class LDPlayerController:
    def __init__(self, adb_path="D:/APP/LDPlayer9/adb.exe", device_name="LDPlayer", device_address="127.0.0.1:5555"):
        """初始化LDPlayer控制器"""
        self.adb_path = adb_path
        self.device_name = device_name
        self.device_address = device_address
        self.screenshot_path = "screenshot.png"  # 截图保存路径
        self.screen_width = None  # 屏幕宽度
        self.screen_height = None  # 屏幕高度
        self.ldplayer_path = r"D:\APP\LDPlayer9\dnplayer.exe"  # 模拟器路径
        self.max_retry = 5  # 最大重试次数

        # 连接设备
        self.connect_device()
        # 获取屏幕分辨率
        self.get_screen_resolution()

    def restart_emulator(self):
        """重启模拟器"""
        print("正在重启模拟器...")
        try:
            subprocess.run(["taskkill", "/f", "/im", "dnplayer.exe"],
                           check=True, capture_output=True, text=True)
            print("成功关闭dnplayer.exe进程")
        except subprocess.CalledProcessError as e:
            print(f"关闭dnplayer.exe失败: {e}")

        try:
            os.startfile(self.ldplayer_path)
            print("模拟器启动命令已发送")
            # 等待20秒
            time.sleep(20)
        except Exception as e:
            print(f"启动模拟器失败: {e}")

    def wait_for_emulator_to_start(self, timeout=60):
        """等待模拟器启动完成"""
        print("等待模拟器启动...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.run_adb_command(["devices"])
            if result is not None:
                lines = result.strip().splitlines()
                devices = [line for line in lines if "\tdevice" in line]
                if devices:
                    print("模拟器已启动并连接")
                    return True
            time.sleep(5)
        print("模拟器启动超时")
        return False

    def run_adb_command(self, command, device_specific=True):
        """执行ADB命令"""
        try:
            # 构建完整命令
            if device_specific:
                full_command = [self.adb_path, "-s", self.device_address] + command
            else:
                full_command = [self.adb_path] + command

            # 执行命令，指定编码为utf-8并忽略解码错误
            result = subprocess.run(full_command, capture_output=True, text=True,
                                    encoding='utf-8', errors='ignore', check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_message = f"ADB命令执行失败: {e.stderr}"
            print(error_message)
            # 检查是否是设备离线错误
            if "error: device offline" in e.stderr:
                print("检测到设备离线，正在重启模拟器...")
                self.restart_emulator()
                if self.wait_for_emulator_to_start():
                    # 重新连接设备
                    if self.connect_device():
                        # 重新执行命令
                        print("重新执行ADB命令...")
                        try:
                            result = subprocess.run(full_command, capture_output=True, text=True,
                                                    encoding='utf-8', errors='ignore', check=True)
                            return result.stdout.strip()
                        except subprocess.CalledProcessError as retry_e:
                            print(f"重试ADB命令失败: {retry_e.stderr}")
            return None
        except Exception as e:
            print(f"执行ADB命令时发生错误: {str(e)}")
            return None

    def connect_device(self, max_retries=3):
        """连接到指定的LDPlayer设备"""
        for attempt in range(max_retries):
            print(f"正在连接到{self.device_name} ({self.device_address})... (尝试 {attempt + 1}/{max_retries})")
            result = self.run_adb_command(["connect", self.device_address], device_specific=False)
            if result and "connected to" in result:
                # 连接成功后等待设备完全启动
                print("等待设备完全启动...")
                time.sleep(3)
                print(f"成功连接到{self.device_name}")
                return True
            else:
                print(f"连接{self.device_name}失败，等待2秒后重试...")
                time.sleep(2)

        print(f"连接{self.device_name}失败，已达到最大重试次数")
        return False

    def wait_for_device(self, timeout=30):
        """等待设备变为在线状态"""
        print("等待设备在线...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.run_adb_command(["get-state"])
            if result and "device" in result:
                print("设备已在线")
                return True
            time.sleep(1)
        print("设备未在指定时间内变为在线状态")
        return False

    def get_screen_resolution(self):
        """获取屏幕分辨率"""
        print("获取屏幕分辨率...")
        result = self.run_adb_command(["shell", "wm", "size"])
        if result and "Physical size:" in result:
            size_str = result.split(": ")[1].strip()
            try:
                self.screen_width, self.screen_height = map(int, size_str.split("x"))
                print(f"屏幕分辨率: {self.screen_width}x{self.screen_height}")
                return True
            except ValueError:
                print("解析屏幕分辨率失败")
                return False
        else:
            print("获取屏幕分辨率失败")
            return False

    def take_screenshot(self):
        """截取屏幕并保存到本地"""
        try:
            print("正在截取屏幕...")
            # 使用ADB命令截图并保存到设备
            device_screenshot_path = "/sdcard/screenshot.png"
            self.run_adb_command(["shell", "screencap", "-p", device_screenshot_path])

            # 将截图从设备拉取到本地
            self.run_adb_command(["pull", device_screenshot_path, self.screenshot_path])

            # 删除设备上的截图
            self.run_adb_command(["shell", "rm", device_screenshot_path])

            print(f"截图已保存到 {self.screenshot_path}")
            return True
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return False

    def load_screenshot(self):
        """加载截图为OpenCV图像对象，处理分辨率变化"""
        if not os.path.exists(self.screenshot_path):
            print("截图文件不存在，请先执行截图")
            return None

        # 使用OpenCV读取图像
        image = cv2.imread(self.screenshot_path)
        if image is None:
            print("无法加载截图")
            return None

        # 检查图像分辨率是否与设备分辨率匹配
        img_height, img_width = image.shape[:2]
        # 确保设备分辨率已正确获取再进行比较
        if self.screen_width and self.screen_height and (
                img_width != self.screen_width or img_height != self.screen_height):
            print(
                f"截图分辨率({img_width}x{img_height})与设备分辨率({self.screen_width}x{self.screen_height})不匹配，正在调整...")
            # 调整图像大小以匹配设备分辨率
            try:
                image = cv2.resize(image, (self.screen_width, self.screen_height))
            except cv2.error as e:
                print(f"调整图像大小时出错: {e}")
                return None

        return image

    def find_image_in_screenshot(self, target_image_path, threshold=0.8):
        """在截图中查找目标图像

        Args:
            target_image_path: 目标图像路径
            threshold: 匹配阈值，0-1之间，值越高匹配度要求越严格

        Returns:
            找到的位置坐标(x, y)，如果未找到返回None
        """
        # 加载截图
        screenshot = self.load_screenshot()
        if screenshot is None:
            return None

        # 检查目标图像是否存在
        if not os.path.exists(target_image_path):
            print(f"目标图像不存在: {target_image_path}")
            return None

        # 加载目标图像
        target = cv2.imread(target_image_path)
        if target is None:
            print(f"无法加载目标图像: {target_image_path}")
            return None

        # 获取目标图像和截图的尺寸
        target_height, target_width = target.shape[:2]
        screenshot_height, screenshot_width = screenshot.shape[:2]

        # 检查模板尺寸是否大于原图尺寸
        if target_height > screenshot_height or target_width > screenshot_width:
            print(f"目标图像尺寸({target_width}x{target_height})大于截图尺寸({screenshot_width}x{screenshot_height})")
            # 尝试调整目标图像大小以适应截图
            if screenshot_width > 10 and screenshot_height > 10:  # 确保截图有合理尺寸
                # 按比例缩放目标图像，使其适合截图
                scale_x = screenshot_width / target_width
                scale_y = screenshot_height / target_height
                scale = min(scale_x, scale_y, 1.0) * 0.9  # 留一些边距，不超过原尺寸

                new_width = int(target_width * scale)
                new_height = int(target_height * scale)

                target = cv2.resize(target, (new_width, new_height))
                print(f"已调整目标图像尺寸为: {new_width}x{new_height}")

                # 重新获取尺寸
                target_height, target_width = target.shape[:2]

        # 使用模板匹配查找目标图像
        result = cv2.matchTemplate(screenshot, target, cv2.TM_CCOEFF_NORMED)

        # 找到匹配度超过阈值的位置
        locations = np.where(result >= threshold)

        # 如果找到匹配
        if len(locations[0]) > 0:
            # 获取第一个匹配的位置（最左上角的点）
            top_left = (locations[1][0], locations[0][0])

            # 计算目标图像中心位置
            center_x = top_left[0] + target_width // 2
            center_y = top_left[1] + target_height // 2

            print(f"在位置 ({center_x}, {center_y}) 找到目标图像")
            return (center_x, center_y)
        else:
            print("未找到目标图像")
            return None

    def perform_click(self, position):
        """执行点击操作

        Args:
            position: 坐标位置，(x, y)

        Returns:
            操作是否成功
        """
        if not position:
            print("未指定点击位置")
            return False

        x, y = position

        # 确保坐标在有效范围内
        if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
            print(f"无效的坐标位置: ({x}, {y})")
            return False

        print(f"执行点击操作: ({x}, {y})")

        # 执行ADB点击命令
        result = self.run_adb_command(["shell", f"input tap {x} {y}"])
        return result is not None

    def click_center(self):
        """点击屏幕中心位置
        
        Returns:
            操作是否成功
        """
        if not self.screen_width or not self.screen_height:
            print("屏幕分辨率未获取，无法点击中心位置")
            return False

        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        print("点击屏幕中心!!")
        print(f"点击屏幕中心位置: ({center_x}, {center_y})")
        return self.perform_click((center_x, center_y))


def main():
    close_ldplayer_service()
    find_and_kill_port(5555)
    close_ldplayer_processes()
    # 写一个脚本检测是否可以ping通baidu.com,不能的话直接return
    if not is_connected_http:
        return
    else:
        print("有网络")

    # 创建控制器实例
    controller = LDPlayerController()
    controller.restart_emulator()
    isHome = False
    isADB = False

    # 检测ADB连接状态,5次失败尝试关闭进程dnplayer.exe并重新启动模拟器
    retry_count = 0

    # 初始连接检查
    while not isADB and retry_count < controller.max_retry:
        try:
            result = controller.run_adb_command(["devices"], device_specific=False)
            if result is not None:  # 确保命令执行成功
                lines = result.strip().splitlines()
                # 跳过标题行，检查是否有设备处于 "device" 状态
                devices = [line for line in lines if "\tdevice" in line]
                if devices:
                    print("已连接ADB")
                    isADB = True
                else:
                    print("未连接ADB，请检查LDPlayer是否已启动")
                    retry_count += 1
                    if retry_count >= controller.max_retry:
                        main()
                        # 等待模拟器启动
                        print("等待模拟器启动...")
                        if controller.wait_for_emulator_to_start():
                            break
            else:
                print("ADB命令执行失败")
                retry_count += 1
                if retry_count >= controller.max_retry:
                    main()
                    # 等待模拟器启动
                    print("等待模拟器启动...")
                    if controller.wait_for_emulator_to_start():
                        break
        except Exception as e:
            print(f"ADB命令执行异常: {e}")
            retry_count += 1
            if retry_count >= controller.max_retry:
                main()
                # 等待模拟器启动
                print("等待模拟器启动...")
                if controller.wait_for_emulator_to_start():
                    break

        if not isADB and retry_count < controller.max_retry:
            time.sleep(2)  # 增加等待时间

    if not isADB:
        print("ADB连接失败，已达到最大重试次数")

    # while not isADB:
    #     result = controller.run_adb_command(["devices"])
    #     if result and "device" in result:
    #         print("已连接ADB")
    #         isADB=True
    #     else:
    #         print("未连接ADB，请检查LDPlayer是否已启动")
    #         time.sleep(1)

    if controller.connect_device():
        # 等待设备完全启动并重新获取屏幕分辨率
        if controller.wait_for_device():
            # 重新获取屏幕分辨率
            if not controller.get_screen_resolution():
                print("无法获取设备屏幕分辨率")
            else:
                print(f"设备屏幕分辨率: {controller.screen_width}x{controller.screen_height}")

        while not isHome:
            controller.take_screenshot()
            # 如果能找到截取的图片screenshot.png中有home的特征fig/Home_feature.png则认为在home界面
            if controller.find_image_in_screenshot("fig/Home_feature.png"):
                isHome = True
                print("已进入home界面")
            else:
                print("未进入home界面，尝试返回home")
                # 使用ADB的home键
                controller.run_adb_command(["shell", "input keyevent KEYCODE_HOME"])
                time.sleep(5)

        # 截取屏幕
        controller.take_screenshot()

        # 查找目标图像（fig文件夹下的fgo图标.png）
        # target_path = os.path.join("fig", "fgoLogo.png")
        target_path = "fig/fgoLogo.png"
        target_position = controller.find_image_in_screenshot(target_path)

        print("点击fgo图标!!")
        # 如果找到目标，执行点击
        if target_position:
            controller.perform_click(target_position)
        # 等待fgo启动，40s
        time.sleep(40)

        # 之后每一秒检测一次是否在fig/clickgame.png界面,如果是,则点击,重试的总时间超过60s,重启模拟器,从头开始运行main
        restart_count = 0
        max_restarts = 3
        start_time = time.time()
        timeout = 120  # 60秒超时时间

        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                print("操作超时，重新重启模拟器")
                main()
                if controller.wait_for_emulator_to_start():
                    print("模拟器已重新启动，重新开始运行main")
                    main()
                    return
            try:
                controller.take_screenshot()
                # 1. 获取“clickgame”的坐标（而非复用旧的target_position）
                clickgame_pos = controller.find_image_in_screenshot("fig/clickgame.png")
                if clickgame_pos:  # 2. 若找到，使用新坐标点击
                    print("找到请点击游戏界面，执行点击...")
                    controller.perform_click(clickgame_pos)  # 此处用新坐标
                    print("等待加载...")
                    time.sleep(9)
                    break
                else:
                    print("未找到点击游戏界面，继续等待...")
                    time.sleep(0.5)
                    continue
            except KeyboardInterrupt:
                print("用户中断操作")
                raise
            except Exception as e:
                print(f"执行过程中出现异常: {e}")
                restart_count += 1
                if restart_count > max_restarts:
                    print("异常重启次数过多，终止操作")
                    break
                time.sleep(10)  # 短暂等待后重试
                continue
        controller.take_screenshot()

        # ========================================================================================================================
        restart_count = 0
        max_restarts = 3
        start_time = time.time()

        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                print("操作超时，重新重启模拟器")
                main()
                if controller.wait_for_emulator_to_start():
                    print("模拟器已重新启动，重新开始运行main")
                    main()
                    return
            try:
                controller.take_screenshot()
                # 1. 获取“clickgame”的坐标（而非复用旧的target_position）
                pos = controller.find_image_in_screenshot("fig/clickScreen.png")
                if pos:  # 2. 若找到，使用新坐标点击
                    print("找到请点击屏幕，执行点击...")
                    # 根据分辨率点击屏幕正中心
                    controller.click_center()
                    print("等待加载...")
                    time.sleep(9)
                    break
                else:
                    print("未找到点击屏幕，继续等待...")
                    time.sleep(0.5)
                    continue
            except KeyboardInterrupt:
                print("用户中断操作")
                raise
            except Exception as e:
                print(f"执行过程中出现异常: {e}")
                restart_count += 1
                if restart_count > max_restarts:
                    print("异常重启次数过多，终止操作")
                    break
                time.sleep(10)  # 短暂等待后重试
                continue
        controller.take_screenshot()
        # ========================================================================================================================
        #     截图,然后每秒钟识别一次"fig/gongGao.png",识别到则点击,设置最长时60秒
        start_time = time.time()
        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                print("操作超时，重新重启模拟器")
                main()
                if controller.wait_for_emulator_to_start():
                    print("模拟器已重新启动，重新开始运行main")
                    main()
                    return
            controller.take_screenshot()
            if controller.find_image_in_screenshot("fig/gongGao.png"):
                print("找到公告，执行关闭...")
                # 使用系统返回键
                controller.run_adb_command(["shell", "input keyevent KEYCODE_BACK"])
                print("等待加载...")
                time.sleep(5)
                break
            else:
                print("未找到公告，继续等待...")
                time.sleep(0.5)

        # ========================================================================================================================

        print("开始疯狂执行返回键,直到是否退出")
        start_time = time.time()
        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                print("操作超时!!")

            controller.take_screenshot()
            if controller.find_image_in_screenshot("fig/shiFouTuiChu.png"):
                print("找到是否退出按钮!!!")
                # 使用系统返回键
                controller.run_adb_command(["shell", "input keyevent KEYCODE_BACK"])
                print("等待加载...")
                time.sleep(5)
                break
            else:
                print("未找到是否退出按钮，继续返回!")
                controller.run_adb_command(["shell", "input keyevent KEYCODE_BACK"])
                time.sleep(0.5)
        close_dnplayer()
    print("程序执行完毕")


def close_dnplayer():
    """关闭dnplayer.exe进程"""
    process_name = "dnplayer.exe"
    found = False

    try:
        # 遍历所有正在运行的进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # 检查进程名是否匹配（不区分大小写）
                if proc.info['name'].lower() == process_name.lower():
                    found = True
                    print(f"发现进程 {process_name}，PID: {proc.info['pid']}")

                    # 尝试终止进程
                    process = psutil.Process(proc.info['pid'])
                    process.terminate()

                    # 等待进程终止
                    try:
                        process.wait(timeout=5)
                        print(f"进程 {process_name} (PID: {proc.info['pid']}) 已成功关闭")
                    except psutil.TimeoutExpired:
                        # 超时则强制杀死
                        process.kill()
                        print(f"进程 {process_name} (PID: {proc.info['pid']}) 已被强制关闭")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                # 忽略无权限访问的进程或已结束的进程
                continue
    except Exception as e:
        print(f"处理进程时发生错误: {e}")
        return

    if not found:
        print(f"未发现运行中的 {process_name} 进程")
    else:
        print("操作完成")

def close_ldplayer_service():
    """关闭ldplayerservice.exe进程"""
    try:
        # 遍历所有正在运行的进程
        for process in psutil.process_iter(['pid', 'name']):
            # 检查进程名是否匹配
            if process.info['name'].lower() == 'ldplayerservice.exe':
                print(f"找到ldplayerservice.exe进程，PID: {process.info['pid']}")
                # 终止进程
                process.terminate()
                # 等待进程终止
                try:
                    process.wait(timeout=5)
                    print("ldplayerservice.exe进程已成功关闭")
                except psutil.TimeoutExpired:
                    # 如果终止超时，强制杀死进程
                    process.kill()
                    print("强制关闭ldplayerservice.exe进程")
    except psutil.NoSuchProcess:
        print("进程已终止")
    except Exception as e:
        print(f"关闭进程时发生错误: {e}")


def find_and_kill_port(port):
    """查找并关闭占用指定端口的进程，兼容不同psutil版本"""
    try:
        # 确定TCP连接类型常量（兼容新旧版本psutil）
        if hasattr(psutil, 'CONN_TCP'):
            tcp_conn_type = psutil.CONN_TCP
        else:
            # 旧版本psutil使用数值1表示TCP连接
            tcp_conn_type = 1

        # 遍历所有进程的网络连接
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                # 检查每个连接
                for conn in proc.info['connections']:
                    # 检查是否是TCP连接且端口匹配
                    if conn.type == tcp_conn_type and conn.laddr.port == port:
                        print(f"发现占用端口 {port} 的进程:")
                        print(f"PID: {proc.info['pid']}, 名称: {proc.info['name']}")

                        # 尝试终止进程
                        try:
                            process = psutil.Process(proc.info['pid'])
                            process.terminate()
                            # 等待进程终止
                            process.wait(timeout=5)
                            print(f"进程 {proc.info['pid']} 已成功关闭")
                            return True
                        except psutil.TimeoutExpired:
                            # 超时则强制杀死
                            process.kill()
                            print(f"进程 {proc.info['pid']} 已被强制关闭")
                            return True
                        except Exception as e:
                            print(f"关闭进程时出错: {e}")
                            return False
            except (psutil.AccessDenied, psutil.NoSuchProcess, KeyError):
                # 忽略无权限或已结束的进程
                continue

    except Exception as e:
        print(f"检查端口时发生错误: {e}")
        return False

    print(f"未发现占用端口 {port} 的进程")
    return False


def close_ldplayer_processes():
    """关闭Ld9BoxHeadless.exe和Ld9BoxSVC.exe进程"""
    # 要关闭的进程名称列表
    target_processes = [
        "Ld9BoxHeadless.exe",
        "Ld9BoxSVC.exe"
    ]

    for process_name in target_processes:
        try:
            # 遍历所有进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 检查进程名是否匹配（不区分大小写）
                    if proc.info['name'].lower() == process_name.lower():
                        print(f"发现进程 {process_name}，PID: {proc.info['pid']}")

                        # 尝试终止进程
                        process = psutil.Process(proc.info['pid'])
                        process.terminate()

                        # 等待进程终止
                        try:
                            process.wait(timeout=5)
                            print(f"进程 {process_name} (PID: {proc.info['pid']}) 已成功关闭")
                        except psutil.TimeoutExpired:
                            # 超时则强制杀死
                            process.kill()
                            print(f"进程 {process_name} (PID: {proc.info['pid']}) 已被强制关闭")
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    # 忽略无权限访问的进程或已结束的进程
                    continue
        except Exception as e:
            print(f"处理进程 {process_name} 时发生错误: {e}")

    print("关闭Ld9BoxHeadless完成")


if __name__ == "__main__":
    main()
