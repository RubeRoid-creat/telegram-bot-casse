# Скрипт для создания и настройки SSH ключа

Write-Host "🔑 Настройка SSH ключа для сервера..." -ForegroundColor Green
Write-Host ""

# Проверка наличия ключа
$keyPath = "$env:USERPROFILE\.ssh\id_rsa"
if (Test-Path $keyPath) {
    Write-Host "✅ SSH ключ уже существует: $keyPath" -ForegroundColor Yellow
    $useExisting = Read-Host "Использовать существующий ключ? (Y/N)"
    if ($useExisting -ne "Y" -and $useExisting -ne "y") {
        $keyPath = "$env:USERPROFILE\.ssh\id_rsa_bot"
    }
} else {
    $keyPath = "$env:USERPROFILE\.ssh\id_rsa"
}

# Создание ключа если его нет
if (-not (Test-Path $keyPath)) {
    Write-Host "📝 Создание нового SSH ключа..." -ForegroundColor Cyan
    ssh-keygen -t rsa -b 4096 -f $keyPath -N '""'
    Write-Host "✅ Ключ создан: $keyPath" -ForegroundColor Green
}

# Копирование публичного ключа на сервер
Write-Host ""
Write-Host "📤 Копирование публичного ключа на сервер..." -ForegroundColor Cyan
Write-Host "Введите пароль root при запросе" -ForegroundColor Yellow
Write-Host ""

$publicKey = Get-Content "$keyPath.pub"
Write-Host "Публичный ключ:" -ForegroundColor Yellow
Write-Host $publicKey -ForegroundColor Gray
Write-Host ""

# Попытка скопировать ключ
ssh-copy-id -i "$keyPath.pub" root@212.74.227.208

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ SSH ключ успешно настроен!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Теперь можно загружать файлы командой:" -ForegroundColor Yellow
    Write-Host "scp -i $keyPath -r * root@212.74.227.208:/root/telegram-bot/" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "⚠️  Автоматическое копирование не удалось." -ForegroundColor Yellow
    Write-Host "Скопируйте публичный ключ вручную:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Подключитесь к серверу:" -ForegroundColor Cyan
    Write-Host "   ssh root@212.74.227.208" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. На сервере выполните:" -ForegroundColor Cyan
    Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Gray
    Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Вставьте этот ключ:" -ForegroundColor Cyan
    Write-Host $publicKey -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Сохраните (Ctrl+X, Y, Enter)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "5. Установите права:" -ForegroundColor Cyan
    Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
    Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Gray
}

