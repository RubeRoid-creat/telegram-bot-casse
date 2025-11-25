"""
Скрипт для запуска бота как службы Windows
Используйте: python run_bot_service.py install для установки
Используйте: python run_bot_service.py start для запуска
Используйте: python run_bot_service.py stop для остановки
"""
import sys
import os
import subprocess
from pathlib import Path

def install_service():
    """Установка бота как службы Windows"""
    script_path = Path(__file__).parent / "main.py"
    python_path = sys.executable
    
    # Создание VBS скрипта для запуска в фоне
    vbs_script = f"""
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "{python_path} {script_path}", 0, False
Set WshShell = Nothing
"""
    
    vbs_path = Path(__file__).parent / "start_bot.vbs"
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_script)
    
    print(f"Скрипт запуска создан: {vbs_path}")
    print("Для автозапуска добавьте этот файл в автозагрузку Windows:")
    print("Win+R -> shell:startup -> скопируйте start_bot.vbs туда")


def start_service():
    """Запуск бота"""
    script_path = Path(__file__).parent / "main.py"
    subprocess.Popen([sys.executable, str(script_path)], 
                     creationflags=subprocess.CREATE_NO_WINDOW)
    print("Бот запущен в фоновом режиме")


def stop_service():
    """Остановка бота"""
    subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", 
                   f"COMMANDLINE eq *main.py*"], 
                  capture_output=True)
    print("Бот остановлен")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python run_bot_service.py install - создать скрипт автозапуска")
        print("  python run_bot_service.py start - запустить бота")
        print("  python run_bot_service.py stop - остановить бота")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "install":
        install_service()
    elif command == "start":
        start_service()
    elif command == "stop":
        stop_service()
    else:
        print(f"Неизвестная команда: {command}")

