import aiosqlite
from datetime import datetime
from typing import Optional, Tuple

DB_NAME = "casse.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_type TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username TEXT
            )
        """)
        await db.commit()


async def add_transaction(
    chat_id: int,
    amount: float,
    payment_type: str,
    operation_type: str,
    description: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None
):
    """Добавление транзакции"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO transactions 
            (chat_id, amount, payment_type, operation_type, description, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, amount, payment_type, operation_type, description, user_id, username))
        await db.commit()


async def get_balance(chat_id: int) -> Tuple[float, float]:
    """Получение баланса наличных и безналичных средств"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                SUM(CASE WHEN payment_type = 'cash' AND operation_type = 'add' THEN amount ELSE 0 END) -
                SUM(CASE WHEN payment_type = 'cash' AND operation_type = 'subtract' THEN amount ELSE 0 END) as cash,
                SUM(CASE WHEN payment_type = 'card' AND operation_type = 'add' THEN amount ELSE 0 END) -
                SUM(CASE WHEN payment_type = 'card' AND operation_type = 'subtract' THEN amount ELSE 0 END) as card
            FROM transactions
            WHERE chat_id = ?
        """, (chat_id,))
        row = await cursor.fetchone()
        cash_balance = row[0] if row[0] else 0.0
        card_balance = row[1] if row[1] else 0.0
        return cash_balance, card_balance


async def get_recent_transactions(chat_id: int, limit: int = 10):
    """Получение последних транзакций"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT amount, payment_type, operation_type, description, created_at, username
            FROM transactions
            WHERE chat_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (chat_id, limit))
        return await cursor.fetchall()


async def reset_balance(chat_id: int):
    """Сброс баланса (удаление всех транзакций для чата)"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM transactions WHERE chat_id = ?", (chat_id,))
        await db.commit()

