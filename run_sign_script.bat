@echo off
:: ������־�ļ�·��
set log_path="E:\Code\pythonProject\pythonProject\ǩ���ű�\log.txt"

:: �����ǰʱ�䵽����̨����־�ļ�����Ϊ�ָ��ߣ�
echo ===================== ��ʼ���У�%date% %time% =====================
echo ===================== ��ʼ���У�%date% %time% ===================== >> %log_path%

echo ����ʹ��ָ��Python��������ǩ���ű�...
:: ����Python�ű�����������ʹ����ض�����־�ļ���׷��ģʽ��
"D:\APP\conda\python.exe" "E:\Code\pythonProject\pythonProject\ǩ���ű�\ǩ���ű�V1.py" >> %log_path% 2>&1

:: �������ʱ�䵽����̨����־�ļ�
echo ===================== ���н�����%date% %time% =====================
echo ===================== ���н�����%date% %time% ===================== >> %log_path%
echo. >> %log_path%  :: ��ӿ��зָ���ͬ�ε�������־

echo �ű�������ϣ���־�ѱ��浽��%log_path%
