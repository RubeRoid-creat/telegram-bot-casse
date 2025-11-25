# Скрипт для ручного копирования SSH ключа на сервер

Write-Host "🔑 Копирование SSH ключа на сервер" -ForegroundColor Green
Write-Host ""

$keyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"

if (-not (Test-Path $keyPath)) {
    Write-Host "❌ SSH ключ не найден: $keyPath" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Ваш публичный ключ:" -ForegroundColor Yellow
Write-Host ""
$publicKey = Get-Content $keyPath
Write-Host $publicKey -ForegroundColor Cyan
Write-Host ""

Write-Host "📝 Инструкция:" -ForegroundColor Yellow
Write-Host "1. Подключитесь к серверу с паролем:" -ForegroundColor White
Write-Host "   ssh root@212.74.227.208" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. На сервере выполните команды:" -ForegroundColor White
Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Cyan
Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Вставьте ключ выше (Ctrl+Shift+V или правой кнопкой мыши)" -ForegroundColor White
Write-Host ""
Write-Host "4. Сохраните файл:" -ForegroundColor White
Write-Host "   Ctrl+X, затем Y, затем Enter" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Установите права:" -ForegroundColor White
Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Cyan
Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Cyan
Write-Host ""
Write-Host "6. Выйдите: exit" -ForegroundColor White
Write-Host ""
Write-Host "7. После этого загрузите файлы:" -ForegroundColor White
Write-Host "   cd `"Z:\Telegram_bot Casse`"" -ForegroundColor Cyan
Write-Host "   scp -r * root@212.74.227.208:/root/telegram-bot/" -ForegroundColor Cyan
Write-Host ""

$copy = Read-Host "Скопировать ключ в буфер обмена? (Y/N)"
if ($copy -eq "Y" -or $copy -eq "y") {
    $publicKey | Set-Clipboard
    Write-Host "✅ Ключ скопирован в буфер обмена!" -ForegroundColor Green
}

