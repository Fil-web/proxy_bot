import os
import json
import secrets
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    BOT_TOKEN = "TEST_MODE"

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

def get_proxy_links(secret):
    """Генерирует ссылки для прокси"""
    tg_link = f"tg://proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={secret}"
    web_link = f"https://t.me/proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={secret}"
    return tg_link, web_link

def get_proxy_keyboard(tg_link, web_link):
    """Создает клавиатуру с кнопками для подключения"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🚀 ПОДКЛЮЧИТЬСЯ К ПРОКСИ",
        url=tg_link
    ))
    
    builder.row(
        InlineKeyboardButton(
            text="🌐 Web-ссылка",
            url=web_link
        )
        # Убрали кнопку "Скопировать ключ", так как ключ уже есть в тексте
    )
    
    builder.row(InlineKeyboardButton(
        text="❓ Как это работает",
        callback_data="help"
    ))
    
    return builder.as_markup()
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
    tg_link, web_link = get_proxy_links(secret)
    
    print(f"\n🔗 Тестовая ссылка прокси:")
    print(f"  TG: {tg_link}")
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
            tg_link, web_link = get_proxy_links(existing_secret)
            
            await message.answer(
                f"🔑 <b>Ваш ключ для подключения готов!</b>\n\n"
                f"<code>{existing_secret}</code>\n\n"
                f"👇 Нажмите кнопку ниже для автоматической настройки прокси:",
                parse_mode="HTML",
                reply_markup=get_proxy_keyboard(tg_link, web_link)
            )
            return
        
        try:
            chat_member = await bot.get_chat_member(CHANNEL_ID, int(user_id))
            if chat_member.status in ['member', 'administrator', 'creator']:
                new_secret = secrets.token_hex(16)
                allowed_users[user_id] = new_secret
                save_allowed_secrets(allowed_users)
                
                tg_link, web_link = get_proxy_links(new_secret)
                
                # Отправляем приветственное сообщение с кнопками
                await message.answer(
                    f"✅ <b>Подписка подтверждена!</b>\n\n"
                    f"🔑 <b>Ваш личный ключ:</b>\n"
                    f"<code>{new_secret}</code>\n\n"
                    f"👇 <b>Нажмите кнопку для подключения:</b>",
                    parse_mode="HTML",
                    reply_markup=get_proxy_keyboard(tg_link, web_link)
                )
                
                # Отправляем дополнительное сообщение с инструкцией (опционально)
                await message.answer(
                    f"📱 <b>Как это работает:</b>\n"
                    f"1️⃣ Нажмите кнопку <b>«ПОДКЛЮЧИТЬСЯ»</b>\n"
                    f"2️⃣ Telegram спросит подтверждение\n"
                    f"3️⃣ Готово! Прокси настроен автоматически\n\n"
                    f"🌐 Если кнопка не работает, используйте Web-ссылку или скопируйте ключ вручную.",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"❌ <b>Подписка не найдена</b>\n\n"
                    f"Чтобы получить доступ к прокси, подпишитесь на канал:\n"
                    f"{CHANNEL_ID}\n\n"
                    f"После подписки нажмите /start снова.",
                    parse_mode="HTML"
                )
        except Exception as e:
            await message.answer(
                "❌ Ошибка проверки подписки\n\n"
                "Пожалуйста, попробуйте позже или обратитесь к администратору."
            )
            print(f"Error checking subscription for user {user_id}: {e}")

    @dp.message(Command("stats"))
    async def cmd_stats(message: Message):
        """Статистика для администратора"""
        # Простая проверка на админа (можно добавить список админов)
        if message.from_user.id == 123456789:  # Замените на свой ID
            allowed_users = load_allowed_secrets()
            active_count = len(allowed_users)
            
            stats_text = (
                f"📊 <b>Статистика прокси</b>\n\n"
                f"👥 Всего пользователей: <b>{active_count}</b>\n"
                f"🆔 Последние 5:\n"
            )
            
            # Добавляем последних 5 пользователей
            for uid, secret in list(allowed_users.items())[-5:]:
                stats_text += f"  • <code>{uid}</code>: {secret[:8]}...\n"
            
            await message.answer(stats_text, parse_mode="HTML")
        else:
            await message.answer("⛔ Эта команда только для администраторов")

    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery):
        """Обработка нажатий на кнопки"""
        if callback.data.startswith("copy_"):
            # Показываем ключ в уведомлении
            await callback.answer(
                "Ключ скопирован! Вставьте его в настройках Telegram",
                show_alert=False
            )
        elif callback.data == "help":
            await callback.message.answer(
                "❓ <b>Как пользоваться прокси:</b>\n\n"
                "1️⃣ Нажмите кнопку «ПОДКЛЮЧИТЬСЯ»\n"
                "2️⃣ Telegram автоматически откроет настройки\n"
                "3️⃣ Нажмите «Добавить прокси»\n"
                "4️⃣ Готово! Telegram будет работать через прокси\n\n"
                "🌐 <b>Ручная настройка:</b>\n"
                "Сервер: {PROXY_SERVER}\n"
                "Порт: {PROXY_PORT}\n"
                "Секретный ключ: скопируйте из сообщения",
                parse_mode="HTML"
            )
            await callback.answer()

# ... (остальные функции остаются без изменений)

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