#!/bin/bash
# Остановка бота

cd "$(dirname "$0")"

if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 Остановка бота (PID: $PID)..."
        kill $PID
        rm bot.pid
        echo "✅ Бот остановлен"
    else
        echo "⚠️  Процесс с PID $PID не найден"
        rm bot.pid
    fi
else
    echo "⚠️  Файл bot.pid не найден. Попытка найти процесс..."
    pkill -f "python3 main.py"
    echo "✅ Попытка остановки завершена"
fi

