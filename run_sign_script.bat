@echo off
:: 定义日志文件路径
set log_path="E:\Code\pythonProject\pythonProject\签到脚本\log.txt"

:: 输出当前时间到控制台和日志文件（作为分隔线）
echo ===================== 开始运行：%date% %time% =====================
echo ===================== 开始运行：%date% %time% ===================== >> %log_path%

echo 正在使用指定Python环境运行签到脚本...
:: 运行Python脚本，并将输出和错误重定向到日志文件（追加模式）
"D:\APP\conda\python.exe" "E:\Code\pythonProject\pythonProject\签到脚本\签到脚本V1.py" >> %log_path% 2>&1

:: 输出结束时间到控制台和日志文件
echo ===================== 运行结束：%date% %time% =====================
echo ===================== 运行结束：%date% %time% ===================== >> %log_path%
echo. >> %log_path%  :: 添加空行分隔不同次的运行日志

echo 脚本运行完毕！日志已保存到：%log_path%
