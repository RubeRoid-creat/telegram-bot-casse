#!/bin/bash
# Проверка статуса бота

cd "$(dirname "$0")"

if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Бот работает (PID: $PID)"
        echo "📋 Последние строки лога:"
        tail -n 5 logs/bot.log 2>/dev/null || echo "Логи не найдены"
    else
        echo "❌ Бот не работает (процесс не найден)"
        rm bot.pid
    fi
else
    echo "❌ Бот не запущен (файл bot.pid не найден)"
fi

