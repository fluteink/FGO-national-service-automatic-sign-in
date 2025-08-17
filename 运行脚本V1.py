import subprocess
import datetime
import time
import os
import sys
import io
from chardet import detect  # 需要安装chardet库：pip install chardet

# 配置路径（根据实际情况修改）
CONDA_PYTHON_PATH = r"D:\APP\conda\python.exe"  # 指定的Python解释器路径
TARGET_SCRIPT_PATH = r"E:\Code\pythonProject\pythonProject\签到脚本\签到脚本V1.py"  # 签到脚本路径
LOG_PATH = r"E:\Code\pythonProject\pythonProject\签到脚本\log.txt"  # 日志文件路径


def write_log(content, is_console=True):
    """写入日志（同时输出到控制台和日志文件）"""
    # 控制台输出
    if is_console:
        print(content)
    # 日志文件写入（追加模式，utf-8编码）
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(content + "\n")


def detect_encoding(byte_data):
    """检测字节数据的编码"""
    result = detect(byte_data)
    return result['encoding'] or 'utf-8'  # 默认使用utf-8


def run_sign_script():
    """运行签到脚本并记录日志"""
    # 记录开始时间（精确到毫秒）
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    start_line = f"===================== 开始运行：{start_time} ====================="
    write_log(start_line)

    # 提示信息
    write_log("正在使用指定Python环境运行签到脚本...")

    try:
        # 调用指定Python解释器运行签到脚本，捕获输出和错误（先获取字节数据）
        result = subprocess.run(
            [CONDA_PYTHON_PATH, TARGET_SCRIPT_PATH],
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.STDOUT,  # 合并标准错误到标准输出
            timeout=3600  # 超时时间（1小时，可根据脚本实际运行时间调整）
        )

        # 检测输出编码并解码
        byte_output = result.stdout
        encoding = detect_encoding(byte_output)

        # 尝试用检测到的编码解码，失败则使用utf-8并忽略错误
        try:
            script_output = byte_output.decode(encoding)
        except UnicodeDecodeError:
            write_log(f"\n警告：使用检测到的编码({encoding})解码失败，将使用utf-8并忽略错误")
            script_output = byte_output.decode('utf-8', errors='ignore')

        # 记录脚本输出内容
        if script_output:
            write_log("\n【脚本输出内容】：")
            write_log(script_output)
        else:
            write_log("\n【脚本输出内容】：无")

    except subprocess.TimeoutExpired:
        # 处理超时
        error_msg = "\n错误：签到脚本运行超时（超过1小时）"
        write_log(error_msg)
    except Exception as e:
        # 处理其他异常（如脚本不存在、Python路径错误等）
        error_msg = f"\n错误：运行签到脚本时发生异常 - {str(e)}"
        write_log(error_msg)

    # 记录结束时间
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    end_line = f"===================== 运行结束：{end_time} ====================="
    write_log(end_line)
    # 空行分隔不同次运行的日志
    write_log("")


def schedule_daily_run():
    """定时任务：每天4点15分运行签到脚本，主程序持续运行"""
    write_log("定时任务已启动，将每天4点15分自动运行签到脚本（主程序将持续运行）...\n")

    while True:
        # 获取当前时间
        now = datetime.datetime.now()
        # 计算"今天4点15分"的时间对象
        target_time = now.replace(hour=4, minute=15, second=0, microsecond=0)

        if now > target_time:
            target_time += datetime.timedelta(days=1)

        # 计算需要等待的秒数
        wait_seconds = (target_time - now).total_seconds()
        # 显示下次运行时间（方便监控）
        next_run_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        write_log(
            f"下次运行时间：{next_run_str}，将等待 {int(wait_seconds // 3600)}小时{int((wait_seconds % 3600) // 60)}分钟...")

        # 等待到目标时间（阻塞当前进程，不消耗过多资源）
        time.sleep(wait_seconds)

        # 到点后执行签到脚本
        write_log(f"\n====== 到达指定时间 {next_run_str}，开始执行签到脚本 ======")
        run_sign_script()


if __name__ == "__main__":
    # 启动定时任务（程序将一直运行，除非手动关闭）
    schedule_daily_run()
