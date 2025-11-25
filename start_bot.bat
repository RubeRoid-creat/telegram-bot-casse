@echo off
echo Запуск бота для подсчета кассы...
cd /d "%~dp0"
start "Telegram Bot Casse" /min python main.py
echo Бот запущен в фоновом режиме.
echo Окно можно закрыть, бот продолжит работать.
pause

