import aiosqlite
from datetime import datetime
from typing import Optional, Tuple

DB_NAME = "casse.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем основную таблицу транзакций
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
        
        # Проверяем и добавляем новые поля для юнит-экономики (миграция)
        cursor = await db.execute("PRAGMA table_info(transactions)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'category_id' not in column_names:
            await db.execute("ALTER TABLE transactions ADD COLUMN category_id INTEGER")
        if 'quantity' not in column_names:
            await db.execute("ALTER TABLE transactions ADD COLUMN quantity REAL")
        if 'unit_price' not in column_names:
            await db.execute("ALTER TABLE transactions ADD COLUMN unit_price REAL")
        if 'cost' not in column_names:
            await db.execute("ALTER TABLE transactions ADD COLUMN cost REAL")
        
        # Таблица категорий для юнит-экономики
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, name)
            )
        """)
        
        # Индексы для оптимизации запросов
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_chat_category 
            ON transactions(chat_id, category_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_created 
            ON transactions(created_at)
        """)
        
        await db.commit()


async def add_transaction(
    chat_id: int,
    amount: float,
    payment_type: str,
    operation_type: str,
    description: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    category_id: Optional[int] = None,
    quantity: Optional[float] = None,
    unit_price: Optional[float] = None,
    cost: Optional[float] = None
):
    """Добавление транзакции"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO transactions 
            (chat_id, amount, payment_type, operation_type, description, user_id, username,
             category_id, quantity, unit_price, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, amount, payment_type, operation_type, description, user_id, username,
              category_id, quantity, unit_price, cost))
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


# Функции для работы с категориями и юнит-экономикой
async def create_category(chat_id: int, name: str, description: Optional[str] = None) -> Optional[int]:
    """Создание новой категории"""
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            cursor = await db.execute("""
                INSERT INTO categories (chat_id, name, description)
                VALUES (?, ?, ?)
            """, (chat_id, name, description))
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            return None


async def get_categories(chat_id: int):
    """Получение всех категорий для чата"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT id, name, description, created_at
            FROM categories
            WHERE chat_id = ?
            ORDER BY name
        """, (chat_id,))
        return await cursor.fetchall()


async def get_category_by_name(chat_id: int, name: str) -> Optional[Tuple[int, str, Optional[str]]]:
    """Получение категории по имени"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT id, name, description
            FROM categories
            WHERE chat_id = ? AND LOWER(name) = LOWER(?)
        """, (chat_id, name))
        row = await cursor.fetchone()
        return row if row else None


async def delete_category(chat_id: int, category_id: int):
    """Удаление категории"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM categories WHERE id = ? AND chat_id = ?", (category_id, chat_id))
        await db.commit()


async def get_unit_economics_by_category(chat_id: int, category_id: Optional[int] = None, days: int = 30):
    """Расчет юнит-экономики по категориям"""
    async with aiosqlite.connect(DB_NAME) as db:
        date_filter = "datetime(t.created_at) >= datetime('now', '-' || ? || ' days')"
        if category_id:
            cursor = await db.execute(f"""
                SELECT 
                    c.id as category_id,
                    c.name as category_name,
                    COUNT(DISTINCT t.id) as transactions_count,
                    COALESCE(SUM(CASE WHEN t.operation_type = 'add' THEN t.quantity ELSE 0 END), 0) as total_quantity,
                    COALESCE(AVG(CASE WHEN t.operation_type = 'add' AND t.quantity > 0 THEN t.unit_price ELSE NULL END), 0) as avg_unit_price,
                    COALESCE(SUM(CASE WHEN t.operation_type = 'add' THEN t.amount ELSE -t.amount END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN t.operation_type = 'subtract' THEN COALESCE(t.cost, 0) ELSE 0 END), 0) as total_cost,
                    COALESCE(AVG(CASE WHEN t.operation_type = 'add' THEN t.amount ELSE NULL END), 0) as avg_transaction_amount
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.chat_id = ? 
                    AND t.category_id = ?
                    AND {date_filter}
                    AND t.operation_type = 'add'
                GROUP BY c.id, c.name
                ORDER BY total_revenue DESC
            """, (chat_id, category_id, days))
        else:
            cursor = await db.execute(f"""
                SELECT 
                    c.id as category_id,
                    c.name as category_name,
                    COUNT(DISTINCT t.id) as transactions_count,
                    COALESCE(SUM(CASE WHEN t.operation_type = 'add' THEN t.quantity ELSE 0 END), 0) as total_quantity,
                    COALESCE(AVG(CASE WHEN t.operation_type = 'add' AND t.quantity > 0 THEN t.unit_price ELSE NULL END), 0) as avg_unit_price,
                    COALESCE(SUM(CASE WHEN t.operation_type = 'add' THEN t.amount ELSE -t.amount END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN t.operation_type = 'subtract' THEN COALESCE(t.cost, 0) ELSE 0 END), 0) as total_cost,
                    COALESCE(AVG(CASE WHEN t.operation_type = 'add' THEN t.amount ELSE NULL END), 0) as avg_transaction_amount
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.chat_id = ? 
                    AND {date_filter}
                    AND t.operation_type = 'add'
                GROUP BY c.id, c.name
                ORDER BY total_revenue DESC
            """, (chat_id, days))
        return await cursor.fetchall()


async def get_unit_economics_summary(chat_id: int, days: int = 30):
    """Общая статистика юнит-экономики"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(DISTINCT CASE WHEN t.operation_type = 'add' THEN t.id END) as total_transactions,
                COALESCE(SUM(CASE WHEN t.operation_type = 'add' THEN t.quantity ELSE 0 END), 0) as total_units_sold,
                COALESCE(SUM(CASE WHEN t.operation_type = 'add' THEN t.amount ELSE 0 END), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN t.operation_type = 'subtract' THEN COALESCE(t.cost, 0) ELSE 0 END), 0) as total_cost,
                COALESCE(AVG(CASE WHEN t.operation_type = 'add' THEN t.amount ELSE NULL END), 0) as avg_check,
                COALESCE(AVG(CASE WHEN t.operation_type = 'add' AND t.quantity > 0 THEN t.unit_price ELSE NULL END), 0) as avg_unit_price
            FROM transactions t
            WHERE t.chat_id = ? 
                AND datetime(t.created_at) >= datetime('now', '-' || ? || ' days')
        """, (chat_id, days))
        row = await cursor.fetchone()
        if row:
            total_revenue = row[2] or 0
            total_cost = row[3] or 0
            profit = total_revenue - total_cost
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
            return {
                'transactions': row[0] or 0,
                'units_sold': row[1] or 0,
                'revenue': total_revenue,
                'cost': total_cost,
                'profit': profit,
                'margin': margin,
                'avg_check': row[4] or 0,
                'avg_unit_price': row[5] or 0
            }
        return None

