"""
Скрипт миграции базы данных для добавления полей юнит-экономики
"""
import aiosqlite
import asyncio

DB_NAME = "casse.db"


async def migrate():
    """Миграция базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем наличие новых полей
        cursor = await db.execute("PRAGMA table_info(transactions)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Добавляем новые поля, если их нет
        if 'category_id' not in column_names:
            print("Добавление поля category_id...")
            await db.execute("ALTER TABLE transactions ADD COLUMN category_id INTEGER")
            await db.commit()
        
        if 'quantity' not in column_names:
            print("Добавление поля quantity...")
            await db.execute("ALTER TABLE transactions ADD COLUMN quantity REAL")
            await db.commit()
        
        if 'unit_price' not in column_names:
            print("Добавление поля unit_price...")
            await db.execute("ALTER TABLE transactions ADD COLUMN unit_price REAL")
            await db.commit()
        
        if 'cost' not in column_names:
            print("Добавление поля cost...")
            await db.execute("ALTER TABLE transactions ADD COLUMN cost REAL")
            await db.commit()
        
        # Проверяем наличие таблицы категорий
        cursor = await db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='categories'
        """)
        if not await cursor.fetchone():
            print("Создание таблицы categories...")
            await db.execute("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, name)
                )
            """)
            await db.commit()
        
        # Создаем индексы
        print("Создание индексов...")
        try:
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_chat_category 
                ON transactions(chat_id, category_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_created 
                ON transactions(created_at)
            """)
            await db.commit()
        except Exception as e:
            print(f"Предупреждение при создании индексов: {e}")
        
        print("Миграция завершена успешно!")


if __name__ == "__main__":
    asyncio.run(migrate())

