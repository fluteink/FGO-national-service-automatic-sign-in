import subprocess
import os
import time

def test_restart_emulator():
    """测试restart_emulator函数"""
    ldplayer_path = r"D:\APP\LDPlayer9\dnplayer.exe"
    
    print("测试关闭dnplayer.exe进程...")
    try:
        # 尝试关闭dnplayer.exe进程
        result = subprocess.run(["taskkill", "/f", "/im", "dnplayer.exe"],
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("成功关闭dnplayer.exe进程")
        else:
            print("未找到dnplayer.exe进程或关闭失败")
            print(f"错误信息: {result.stderr}")
    except Exception as e:
        print(f"关闭dnplayer.exe时发生异常: {e}")
    
    print("\n等待3秒...")
    time.sleep(3)
    
    print("测试启动模拟器...")
    try:
        # 尝试启动模拟器
        if os.path.exists(ldplayer_path):
            os.startfile(ldplayer_path)
            print("模拟器启动命令已发送")
        else:
            print(f"模拟器路径不存在: {ldplayer_path}")
    except Exception as e:
        print(f"启动模拟器时发生异常: {e}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_restart_emulator()