# Быстрая настройка Git репозитория

Write-Host "🚀 Настройка Git репозитория" -ForegroundColor Green
Write-Host ""

# Проверка конфигурации Git
$userName = git config user.name
$userEmail = git config user.email

if (-not $userName -or -not $userEmail) {
    Write-Host "⚠️  Git не настроен. Нужно указать имя и email." -ForegroundColor Yellow
    Write-Host ""
    $userName = Read-Host "Введите ваше имя для Git"
    $userEmail = Read-Host "Введите ваш email для Git"
    
    git config --global user.name $userName
    git config --global user.email $userEmail
    
    Write-Host "✅ Git настроен" -ForegroundColor Green
    Write-Host ""
}

Write-Host "📋 Текущие файлы в репозитории:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "📝 Следующие шаги:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Создайте репозиторий на GitHub или GitLab" -ForegroundColor Cyan
Write-Host "   - GitHub: https://github.com/new" -ForegroundColor Gray
Write-Host "   - GitLab: https://gitlab.com/projects/new" -ForegroundColor Gray
Write-Host ""
Write-Host "2. После создания репозитория выполните:" -ForegroundColor Cyan
Write-Host "   git remote add origin https://github.com/ваш_username/telegram-bot-casse.git" -ForegroundColor Gray
Write-Host "   git branch -M main" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "3. На сервере клонируйте репозиторий:" -ForegroundColor Cyan
Write-Host "   ssh root@212.74.227.208" -ForegroundColor Gray
Write-Host "   cd /root" -ForegroundColor Gray
Write-Host "   git clone https://github.com/ваш_username/telegram-bot-casse.git" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Подробные инструкции в файле GIT_DEPLOY.md" -ForegroundColor Yellow

