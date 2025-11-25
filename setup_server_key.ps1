# Скрипт для настройки SSH ключа на сервере и загрузки файлов

Write-Host "🔑 Настройка SSH ключа на сервере..." -ForegroundColor Green
Write-Host ""

$keyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"

if (-not (Test-Path $keyPath)) {
    Write-Host "❌ SSH ключ не найден!" -ForegroundColor Red
    exit 1
}

Write-Host "📤 Копирование публичного ключа на сервер..." -ForegroundColor Cyan
Write-Host "Введите пароль root при запросе" -ForegroundColor Yellow
Write-Host ""

# Читаем публичный ключ
$publicKey = Get-Content $keyPath

# Копируем ключ на сервер
$command = "mkdir -p ~/.ssh && echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"

Write-Host "Выполняется команда на сервере..." -ForegroundColor Gray
ssh root@212.74.227.208 $command

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ SSH ключ успешно настроен на сервере!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Теперь можно загружать файлы без пароля:" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️  Возможно, нужно ввести пароль вручную" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "📦 Загрузка файлов на сервер..." -ForegroundColor Cyan
Write-Host ""

cd "Z:\Telegram_bot Casse"

# Создаем директорию на сервере
ssh root@212.74.227.208 "mkdir -p /root/telegram-bot"

# Загружаем файлы
Write-Host "Загружаю файлы..." -ForegroundColor Gray
scp -r * root@212.74.227.208:/root/telegram-bot/

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Файлы успешно загружены!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Следующие шаги:" -ForegroundColor Yellow
    Write-Host "1. Подключитесь к серверу: ssh root@212.74.227.208" -ForegroundColor Cyan
    Write-Host "2. Перейдите в папку: cd /root/telegram-bot" -ForegroundColor Cyan
    Write-Host "3. Запустите: chmod +x *.sh && ./deploy.sh" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Ошибка при загрузке файлов" -ForegroundColor Red
}

