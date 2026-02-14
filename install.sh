#!/bin/bash

echo "Установка зависимостей Python..."
pip3 install -r requirements.txt

echo "Создание директорий..."
mkdir -p /root/proxy_bot

echo "Установка прав..."
chmod 600 /root/proxy_bot/.env
chmod 644 /root/proxy_bot/bot.py

echo "Готово!"