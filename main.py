import os
import json
import secrets
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# Определяем базовую директорию проекта
BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / '.env'
DATA_DIR = BASE_DIR / 'data'

# Создаем папку для данных, если её нет
DATA_DIR.mkdir(exist_ok=True)

# Загружаем переменные из .env файла
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print(f"⚠️  Файл .env не найден в {ENV_PATH}")
    print("Создайте файл .env с настройками:")

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
PROXY_SERVER = os.getenv('PROXY_SERVER', '162.248.165.76')
PROXY_PORT = int(os.getenv('PROXY_PORT', 443))
SECRETS_FILE = DATA_DIR / 'allowed_users.json'

# Для тестирования можно использовать тестовые значения
if not BOT_TOKEN:
    print("⚠️  BOT_TOKEN не найден, используем тестовый режим")
    BOT_TOKEN = "TEST_MODE"  # Замените на реальный токен для работы

print(f"📁 Директория данных: {DATA_DIR}")
print(f"🔑 Файл с ключами: {SECRETS_FILE}")

# Инициализация бота (только если есть реальный токен)
if BOT_TOKEN and BOT_TOKEN != "TEST_MODE":
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
else:
    print("🔄 Тестовый режим - бот не запущен")
    bot = None
    dp = None

def load_allowed_secrets():
    """Загружает список разрешенных секретов из файла."""
    try:
        if SECRETS_FILE.exists():
            with open(SECRETS_FILE, 'r') as f:
                return json.load(f)
        else:
            print(f"ℹ️  Файл {SECRETS_FILE} не найден, создаем пустой")
            return {}
    except json.JSONDecodeError:
        print(f"⚠️  Ошибка чтения {SECRETS_FILE}, создаем новый")
        return {}

def save_allowed_secrets(secrets_dict):
    """Сохраняет словарь секретов в файл."""
    with open(SECRETS_FILE, 'w') as f:
        json.dump(secrets_dict, f, indent=4)
    print(f"💾 Сохранено {len(secrets_dict)} ключей в {SECRETS_FILE}")

# Тестовые функции для проверки без бота
def test_generate_key():
    """Тестовая генерация ключа"""
    user_id = "test_user_123"
    allowed_users = load_allowed_secrets()
    
    if user_id in allowed_users:
        print(f"🔑 Существующий ключ для {user_id}: {allowed_users[user_id]}")
    else:
        new_secret = secrets.token_hex(16)
        allowed_users[user_id] = new_secret
        save_allowed_secrets(allowed_users)
        print(f"✅ Сгенерирован новый ключ для {user_id}: {new_secret}")
    
    # Показываем все ключи
    print("\n📋 Все сохраненные ключи:")
    for uid, secret in allowed_users.items():
        print(f"  • {uid}: {secret[:8]}...")

def test_proxy_link():
    """Тестовая генерация ссылки прокси"""
    secret = secrets.token_hex(16)
    link = f"tg://proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={secret}"
    web_link = f"https://t.me/proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={secret}"
    
    print(f"\n🔗 Тестовая ссылка прокси:")
    print(f"  TG: {link}")
    print(f"  Web: {web_link}")
    print(f"  Secret: {secret}")

# Команды бота (если бот запущен)
if dp:
    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        user_id = str(message.from_user.id)
        
        allowed_users = load_allowed_secrets()
        
        if user_id in allowed_users:
            existing_secret = allowed_users[user_id]
            await message.answer(
                f"🔑 Ваш действующий ключ: `{existing_secret}`\n"
                f"🔗 Ссылка: `tg://proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={existing_secret}`",
                parse_mode="Markdown"
            )
            return
        
        try:
            chat_member = await bot.get_chat_member(CHANNEL_ID, int(user_id))
            if chat_member.status in ['member', 'administrator', 'creator']:
                new_secret = secrets.token_hex(16)
                allowed_users[user_id] = new_secret
                save_allowed_secrets(allowed_users)
                
                await message.answer(
                    f"✅ Подписка подтверждена!\n"
                    f"🔑 Ключ: `{new_secret}`\n"
                    f"🔗 Ссылка: `tg://proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={new_secret}`",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(f"❌ Подпишитесь на {CHANNEL_ID}")
        except Exception as e:
            await message.answer("Ошибка проверки подписки")
            print(f"Error: {e}")

    @dp.message(Command("stats"))
    async def cmd_stats(message: Message):
        allowed_users = load_allowed_secrets()
        await message.answer(f"📊 Всего пользователей: {len(allowed_users)}")

async def main():
    if bot and dp:
        print("🤖 Запуск бота...")
        await dp.start_polling(bot)
    else:
        print("\n🧪 ТЕСТОВЫЙ РЕЖИМ")
        print("=" * 50)
        test_generate_key()
        test_proxy_link()
        print("\n" + "=" * 50)
        print("✅ Тест завершен. Файлы сохранены в:", DATA_DIR)

if __name__ == '__main__':
    asyncio.run(main())