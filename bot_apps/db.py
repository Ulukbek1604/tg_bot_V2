import aiosqlite
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = 'tg_bot.db'

async def init_db():

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    tg_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS steam_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_name TEXT NOT NULL,
                    st_key TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    count INTEGER NOT NULL,
                    discount INTEGER NOT NULL DEFAULT 0,
                    genre TEXT,
                    region TEXT,
                    image_urls TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_id INTEGER,
                    status TEXT NOT NULL,
                    order_date TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(tg_id),
                    FOREIGN KEY (key_id) REFERENCES steam_keys(id)
                )
            ''')

            await db.execute('INSERT OR IGNORE INTO admins (tg_id, name) VALUES (?, ?)', (1155154067, 'YourName'))
            await db.commit()
            logger.info("Database initialized successfully")
    except aiosqlite.Error as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise



async def ensure_full_database_structure():
    """Добавляет ВСЕ недостающие колонки в таблицы users и steam_keys"""
    async with aiosqlite.connect('tg_bot.db') as db:
        # === Таблица steam_keys ===
        cursor = await db.execute("PRAGMA table_info(steam_keys)")
        steam_cols = [row[1] for row in await cursor.fetchall()]

        additions = []
        if 'sale_active' not in steam_cols:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_active INTEGER DEFAULT 0")
            additions.append("sale_active")
        if 'sale_not' not in steam_cols:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_not TEXT")
            additions.append("sale_not")
        if 'sale_ends_at' not in steam_cols:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_ends_at TEXT")
            additions.append("sale_ends_at")

        # === Таблица users ===
        cursor = await db.execute("PRAGMA table_info(users)")
        user_cols = [row[1] for row in await cursor.fetchall()]

        if 'username' not in user_cols:
            await db.execute("ALTER TABLE users ADD COLUMN username TEXT")
            additions.append("users.username")
        if 'first_name' not in user_cols:
            await db.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
            additions.append("users.first_name")
        if 'balance' not in user_cols:
            await db.execute("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0")
            additions.append("users.balance")
        if 'referrals' not in user_cols:
            await db.execute("ALTER TABLE users ADD COLUMN referrals INTEGER DEFAULT 0")
            additions.append("users.referrals")
        if 'registration_date' not in user_cols:
            await db.execute("ALTER TABLE users ADD COLUMN registration_date TEXT")
            additions.append("users.registration_date")

        if additions:
            await db.commit()
            print(f"Добавлены колонки: {', '.join(additions)}")
        else:
            print("Все колонки уже существуют — база готова!")

        await db.commit()
async def ensure_sale_columns():
    """Безопасно добавляет колонки для акций, если их ещё нет"""
    async with aiosqlite.connect('tg_bot.db') as db:
        # Получаем список существующих колонок
        cursor = await db.execute("PRAGMA table_info(steam_keys)")
        existing_columns = [row[1] for row in await cursor.fetchall()]

        added = []

        if 'sale_active' not in existing_columns:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_active INTEGER DEFAULT 0")
            added.append('sale_active')

        if 'sale_not' not in existing_columns:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_not TEXT")
            added.append('sale_not')

        if 'sale_ends_at' not in existing_columns:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_ends_at TEXT")
            added.append('sale_ends_at')

        if added:
            await db.commit()
            print(f"Добавлены колонки: {', '.join(added)}")
        else:
            print("Все колонки акций уже существуют.")

async def close_db():
    """Пустая функция, так как соединения закрываются автоматически."""
    logger.debug("Database connections are managed automatically")
    pass