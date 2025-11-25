#!/bin/bash
# Перезапуск бота

cd "$(dirname "$0")"

echo "🔄 Перезапуск бота..."
./stop.sh
sleep 2
./start.sh

