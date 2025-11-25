@echo off
echo Остановка бота...
taskkill /FI "WINDOWTITLE eq Telegram Bot Casse*" /T /F
taskkill /FI "IMAGENAME eq python.exe" /FI "COMMANDLINE eq *main.py*" /T /F
echo Бот остановлен.
pause

