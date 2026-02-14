PORT = 443
AD_TAG = "723f82ed76ba30ac87745f90d09d6e09"  # Ваш новый тег

import json
import os
import time

def load_users():
    try:
        with open('/root/proxy_bot/allowed_users.json', 'r') as f:
            users_data = json.load(f)
            # MTProxy ожидает словарь { "имя": "секрет" }
            # Используем новый секретный ключ для всех (или можно индивидуальные)
            return {f"user_{k}": "677680e2f761ae873b5598cf939b9ddf" for k, v in users_data.items()}
    except:
        return {}

USERS = load_users()