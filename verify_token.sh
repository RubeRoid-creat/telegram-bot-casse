#!/bin/bash
# Проверка и тестирование токена бота

cd "$(dirname "$0")"

echo "🔍 Проверка токена бота..."
echo ""

# Проверка файла .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Извлечение токена
if grep -q "BOT_TOKEN=" .env; then
    TOKEN=$(grep "BOT_TOKEN=" .env | cut -d'=' -f2 | tr -d ' ' | tr -d '"' | tr -d "'")
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "your_bot_token_here" ]; then
        echo "❌ Токен не установлен или имеет значение по умолчанию"
        exit 1
    fi
    
    TOKEN_LENGTH=${#TOKEN}
    echo "✅ Токен найден (длина: $TOKEN_LENGTH символов)"
    echo "   Первые 10 символов: ${TOKEN:0:10}..."
    echo ""
    
    # Проверка формата токена (обычно формат: число:буквы_и_цифры)
    if [[ $TOKEN =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        echo "✅ Формат токена корректный"
    else
        echo "⚠️  Формат токена может быть неверным (ожидается: число:буквы_и_цифры)"
    fi
    echo ""
    
    # Тестирование подключения к Telegram API
    echo "🌐 Тестирование подключения к Telegram API..."
    
    # Активация виртуального окружения если есть
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Проверка наличия python и библиотек
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 не найден"
        exit 1
    fi
    
    # Создание временного скрипта для проверки токена
    cat > /tmp/test_token.py << EOF
import asyncio
import sys
from aiogram import Bot

async def test_token():
    try:
        bot = Bot(token="$TOKEN")
        bot_info = await bot.get_me()
        print(f"✅ Токен валидный!")
        print(f"   Бот: @{bot_info.username}")
        print(f"   Имя: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке токена: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_token())
    sys.exit(0 if result else 1)
EOF
    
    if python3 /tmp/test_token.py; then
        echo ""
        echo "✅ Токен работает корректно!"
        rm /tmp/test_token.py
        exit 0
    else
        echo ""
        echo "❌ Токен не работает. Проверьте правильность токена."
        rm /tmp/test_token.py
        exit 1
    fi
    
else
    echo "❌ BOT_TOKEN не найден в файле .env"
    exit 1
fi

