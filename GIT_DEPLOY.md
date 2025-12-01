# Развертывание через Git

## Шаг 1: Создание репозитория на GitHub/GitLab

### Вариант A: GitHub

1. Перейдите на https://github.com
2. Нажмите "New repository"
3. Название: `telegram-bot-casse` (или любое другое)
4. **НЕ** добавляйте README, .gitignore или лицензию (у нас уже есть файлы)
5. Нажмите "Create repository"

### Вариант B: GitLab

1. Перейдите на https://gitlab.com
2. Нажмите "New project" → "Create blank project"
3. Название: `telegram-bot-casse`
4. **НЕ** добавляйте README
5. Нажмите "Create project"

## Шаг 2: Подключение локального репозитория к удаленному

После создания репозитория GitHub/GitLab даст вам URL. Выполните:

```powershell
cd "Z:\Telegram_bot Casse"

# Создайте первый коммит
git commit -m "Initial commit: Telegram bot for cash counting"

# Добавьте удаленный репозиторий
git remote add origin https://github.com/RubeRoid-creat/telegram-bot-casse.git
# или для SSH:
# git remote add origin git@github.com:RubeRoid-creat/telegram-bot-casse.git

# Отправьте код
git branch -M main
git push -u origin main
```

## Шаг 3: Клонирование на сервере

### Подключитесь к серверу:

```powershell
ssh root@212.74.227.208
```

### На сервере выполните:

```bash
# Перейдите в нужную директорию
cd /root

# Клонируйте репозиторий
git clone https://github.com/RubeRoid-creat/telegram-bot-casse.git
# или если используете SSH ключ на сервере:
# git clone git@github.com:RubeRoid-creat/telegram-bot-casse.git

# Перейдите в папку проекта
cd telegram-bot-casse

# Создайте файл .env с токеном бота
nano .env
# Добавьте: BOT_TOKEN=ваш_токен_от_BotFather
# Сохраните: Ctrl+X, Y, Enter

# Сделайте скрипты исполняемыми
chmod +x *.sh

# Запустите развертывание
./deploy.sh

# Запустите бота
./start.sh
```

## Шаг 4: Установка как службы (опционально)

Для автозапуска при перезагрузке:

```bash
sudo ./install_service.sh
sudo systemctl start telegram-bot-casse
sudo systemctl enable telegram-bot-casse
```

## Обновление кода на сервере

Когда внесете изменения:

```bash
# На сервере
cd /root/telegram-bot-casse
git pull
# Если изменились зависимости:
source venv/bin/activate
pip install -r requirements.txt
# Перезапустите бота
./restart.sh
# или если используется служба:
# sudo systemctl restart telegram-bot-casse
```

