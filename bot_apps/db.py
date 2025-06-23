import aiosqlite
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = 'tg_bot.db'

async def init_db():
    """Инициализирует базу данных, создавая необходимые таблицы."""
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
                    region TEXT
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
            # Добавление вашего ID как администратора по умолчанию
            await db.execute('INSERT OR IGNORE INTO admins (tg_id, name) VALUES (?, ?)', (1155154067, 'YourName'))
            await db.commit()
            logger.info("Database initialized successfully")
    except aiosqlite.Error as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

async def close_db():
    """Пустая функция, так как соединения закрываются автоматически."""
    logger.debug("Database connections are managed automatically")
    pass