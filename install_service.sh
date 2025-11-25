#!/bin/bash
# Установка бота как systemd службы

cd "$(dirname "$0")"

USER=$(whoami)
SCRIPT_DIR=$(pwd)
SERVICE_NAME="telegram-bot-casse"

# Создание systemd service файла
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "📝 Создание systemd service файла..."

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Telegram Bot for Cash Counting
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/logs/bot.log
StandardError=append:$SCRIPT_DIR/logs/bot.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service файл создан: $SERVICE_FILE"
echo ""
echo "Для управления службой используйте:"
echo "  sudo systemctl start $SERVICE_NAME    - запуск"
echo "  sudo systemctl stop $SERVICE_NAME     - остановка"
echo "  sudo systemctl restart $SERVICE_NAME  - перезапуск"
echo "  sudo systemctl status $SERVICE_NAME   - статус"
echo "  sudo systemctl enable $SERVICE_NAME   - автозапуск при загрузке"
echo "  sudo systemctl disable $SERVICE_NAME  - отключить автозапуск"
echo ""
echo "Для просмотра логов:"
echo "  sudo journalctl -u $SERVICE_NAME -f"

