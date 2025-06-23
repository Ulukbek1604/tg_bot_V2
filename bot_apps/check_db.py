# check_db.py
import aiosqlite
import asyncio

async def check_db():
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM steam_keys')
        games = await cursor.fetchall()
        print("Игры:", [dict(row) for row in games])
        cursor = await db.execute('SELECT * FROM steam_accounts')
        accounts = await cursor.fetchall()
        print("Аккаунты:", [dict(row) for row in accounts])
        cursor = await db.execute('SELECT * FROM support_tickets')
        tickets = await cursor.fetchall()
        print("Тикеты:", [dict(row) for row in tickets])
        cursor = await db.execute('SELECT * FROM admins')
        admins = await cursor.fetchall()
        print("Админы:", [dict(row) for row in admins])
        cursor = await db.execute('SELECT * FROM users')
        users = await cursor.fetchall()
        print("Пользователи:", [dict(row) for row in users])
        cursor = await db.execute('SELECT * FROM orders')
        orders = await cursor.fetchall()
        print("Заказы:", [dict(row) for row in orders])

if __name__ == "__main__":
    asyncio.run(check_db())