#!/bin/bash
# Запуск бота в фоновом режиме

cd "$(dirname "$0")"

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Проверка наличия .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Создание директории для логов
mkdir -p logs

# Запуск бота в фоне
echo "🚀 Запуск бота..."
nohup python3 main.py > logs/bot.log 2>&1 &
echo $! > bot.pid

echo "✅ Бот запущен! PID: $(cat bot.pid)"
echo "📋 Логи: tail -f logs/bot.log"

