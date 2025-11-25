# Инструкция по развертыванию на сервере

## Быстрое развертывание

### 1. Загрузка файлов на сервер

```bash
# Через SCP
scp -r * user@your-server:/path/to/bot/

# Или через Git
git clone <your-repo> /path/to/bot
cd /path/to/bot
```

### 2. Настройка окружения

```bash
# Сделать скрипты исполняемыми
chmod +x *.sh

# Запустить развертывание
./deploy.sh
```

### 3. Настройка токена бота

Создайте файл `.env`:
```bash
nano .env
```

Добавьте:
```
BOT_TOKEN=your_bot_token_here
```

### 4. Запуск бота

**Вариант 1: Простой запуск (через скрипты)**
```bash
./start.sh      # Запуск
./stop.sh       # Остановка
./restart.sh    # Перезапуск
./status.sh     # Статус
```

**Вариант 2: Как systemd служба (рекомендуется)**
```bash
# Установка службы
sudo ./install_service.sh

# Запуск
sudo systemctl start telegram-bot-casse

# Автозапуск при загрузке системы
sudo systemctl enable telegram-bot-casse

# Проверка статуса
sudo systemctl status telegram-bot-casse

# Просмотр логов
sudo journalctl -u telegram-bot-casse -f
```

## Управление ботом

### Через скрипты:
- `./start.sh` - запуск в фоне
- `./stop.sh` - остановка
- `./restart.sh` - перезапуск
- `./status.sh` - проверка статуса
- Логи: `tail -f logs/bot.log`

### Через systemd:
```bash
sudo systemctl start telegram-bot-casse    # Запуск
sudo systemctl stop telegram-bot-casse     # Остановка
sudo systemctl restart telegram-bot-casse   # Перезапуск
sudo systemctl status telegram-bot-casse   # Статус
sudo journalctl -u telegram-bot-casse -f    # Логи в реальном времени
```

## Обновление бота

```bash
# Остановить бота
./stop.sh
# или
sudo systemctl stop telegram-bot-casse

# Обновить код (через git или загрузить новые файлы)

# Обновить зависимости (если изменились)
source venv/bin/activate
pip install -r requirements.txt

# Запустить снова
./start.sh
# или
sudo systemctl start telegram-bot-casse
```

## Требования

- Python 3.8+
- Доступ к интернету для работы с Telegram API
- Права на создание файлов в директории бота

## Безопасность

- Не коммитьте файл `.env` в Git
- Используйте отдельного пользователя для запуска бота
- Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`

