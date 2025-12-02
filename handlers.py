from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Tuple
import re
import database as db

router = Router()


class TransactionStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_type = State()
    waiting_for_operation_amount = State()
    waiting_for_category = State()
    waiting_for_category_name = State()
    waiting_for_unit_data = State()  # Ожидание количества, цены, расходов


def parse_amount(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Парсинг суммы и типа операции из текста"""
    text = text.strip()
    
    # Проверка на операцию вычитания
    is_subtract = text.startswith('-') or 'минус' in text.lower() or 'вычесть' in text.lower()
    
    # Извлечение числа
    numbers = re.findall(r'\d+[.,]?\d*', text)
    if not numbers:
        return None, None
    
    amount = float(numbers[0].replace(',', '.'))
    if is_subtract:
        amount = -amount
    
    # Определение типа оплаты
    payment_type = None
    if any(word in text.lower() for word in ['нал', 'налич', 'cash']):
        payment_type = 'cash'
    elif any(word in text.lower() for word in ['безнал', 'карт', 'card']):
        payment_type = 'card'
    
    return amount, payment_type


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Создание главной клавиатуры с кнопками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="📋 История", callback_data="history")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_menu"),
            InlineKeyboardButton(text="➖ Вычесть", callback_data="subtract_menu")
        ],
        [
            InlineKeyboardButton(text="📊 Юнит-экономика", callback_data="unit_economics"),
            InlineKeyboardButton(text="📁 Категории", callback_data="categories_menu")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
        ]
    ])
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    await message.answer(
        "💰 Бот для подсчета кассы с юнит-экономикой\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям.\n\n"
        "Быстрый ввод сумм:\n"
        "+1000 нал - добавить 1000 наличными\n"
        "-500 карт - вычесть 500 с карты\n"
        "2000 нал - добавить 2000 наличными\n\n"
        "Юнит-экономика:\n"
        "• Создавайте категории для организации транзакций\n"
        "• Указывайте количество и цену: 500 кол 5 цена 100\n"
        "• Отслеживайте прибыльность по категориям\n\n"
        "Команды:\n"
        "/unit - юнит-экономика\n"
        "/categories - управление категориями",
        reply_markup=get_main_keyboard()
    )


async def show_balance(chat_id: int, message_or_query) -> None:
    """Показать баланс кассы"""
    cash, card = await db.get_balance(chat_id)
    total = cash + card
    
    response = (
        f"💰 Баланс кассы:\n\n"
        f"💵 Наличные: {cash:.2f} ₽\n"
        f"💳 Безналичные: {card:.2f} ₽\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Итого: {total:.2f} ₽"
    )
    
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(response, reply_markup=get_main_keyboard())
        await message_or_query.answer()
    else:
        await message_or_query.answer(response, reply_markup=get_main_keyboard())


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Показать баланс кассы"""
    await show_balance(message.chat.id, message)


def get_payment_type_keyboard(operation: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа оплаты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 Наличные", callback_data=f"{operation}_cash"),
            InlineKeyboardButton(text="💳 Карта", callback_data=f"{operation}_card")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ])
    return keyboard


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    """Добавление средств"""
    await state.update_data(operation="add")
    await message.answer(
        "Выберите тип оплаты:",
        reply_markup=get_payment_type_keyboard("add")
    )
    await state.set_state(TransactionStates.waiting_for_payment_type)


@router.message(Command("subtract"))
async def cmd_subtract(message: Message, state: FSMContext):
    """Вычитание средств"""
    await state.update_data(operation="subtract")
    await message.answer(
        "Выберите тип оплаты:",
        reply_markup=get_payment_type_keyboard("subtract")
    )
    await state.set_state(TransactionStates.waiting_for_payment_type)


async def show_history(chat_id: int, message_or_query) -> None:
    """Показать историю транзакций"""
    transactions = await db.get_recent_transactions(chat_id, 10)
    
    if not transactions:
        text = "История транзакций пуста"
        if isinstance(message_or_query, CallbackQuery):
            await message_or_query.message.edit_text(text, reply_markup=get_main_keyboard())
            await message_or_query.answer()
        else:
            await message_or_query.answer(text, reply_markup=get_main_keyboard())
        return
    
    response = "📋 Последние транзакции:\n\n"
    for trans in transactions:
        amount, payment_type, operation_type, description, created_at, username = trans
        sign = "+" if operation_type == "add" else "-"
        payment_emoji = "💵" if payment_type == "cash" else "💳"
        payment_name = "Нал" if payment_type == "cash" else "Карт"
        user_info = f" ({username})" if username else ""
        
        response += (
            f"{payment_emoji} {sign}{amount:.2f} ₽ ({payment_name}){user_info}\n"
            f"   {description or 'Без описания'}\n"
            f"   {created_at}\n\n"
        )
    
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(response, reply_markup=get_main_keyboard())
        await message_or_query.answer()
    else:
        await message_or_query.answer(response, reply_markup=get_main_keyboard())


@router.message(Command("history"))
async def cmd_history(message: Message):
    """Показать историю транзакций"""
    await show_history(message.chat.id, message)


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    """Сброс баланса (только для админов)"""
    # Проверка прав администратора
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ['administrator', 'creator']:
            await message.answer("❌ Эта команда доступна только администраторам", reply_markup=get_main_keyboard())
            return
    except Exception:
        # В личных чатах проверка не работает, разрешаем
        pass
    
    await db.reset_balance(message.chat.id)
    await message.answer("✅ Баланс сброшен", reply_markup=get_main_keyboard())


def get_unit_economics_hint(operation: str) -> str:
    """Получить подсказку по юнит-данным в зависимости от операции"""
    if operation == "add":
        return (
            "После ввода суммы будет предложено выбрать источник дохода.\n"
            "Примеры: Авито, Сайт, Сарафан, Приложение"
        )
    else:  # subtract
        return (
            "После ввода суммы будет предложено выбрать категорию расхода.\n"
            "Примеры: Закупка, Реклама, Аренда, Зарплата"
        )


def parse_unit_data(text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Парсинг юнит-данных: количество, цена за единицу, расходы"""
    quantity = None
    unit_price = None
    cost = None
    
    text_lower = text.lower()
    
    # Парсинг количества (кол-во, кол, qty, количество)
    quantity_patterns = [
        r'кол[-\s]?([0-9]+[.,]?[0-9]*)',
        r'количество[:\s]+([0-9]+[.,]?[0-9]*)',
        r'qty[:\s]+([0-9]+[.,]?[0-9]*)',
        r'(\d+[.,]?\d*)\s*(шт|ед|units)'
    ]
    for pattern in quantity_patterns:
        match = re.search(pattern, text_lower)
        if match:
            quantity = float(match.group(1).replace(',', '.'))
            break
    
    # Парсинг цены за единицу (цена/ед, цена за, price/unit)
    price_patterns = [
        r'цена[:\s/]+([0-9]+[.,]?[0-9]*)',
        r'price[:\s/]+([0-9]+[.,]?[0-9]*)',
        r'([0-9]+[.,]?[0-9]*)\s*(за\s*единицу|/ед|/unit)'
    ]
    for pattern in price_patterns:
        match = re.search(pattern, text_lower)
        if match:
            unit_price = float(match.group(1).replace(',', '.'))
            break
    
    # Парсинг расходов (расход, расходы, expense)
    cost_patterns = [
        r'расход[=:\s]+([0-9]+[.,]?[0-9]*)',
        r'расходы[=:\s]+([0-9]+[.,]?[0-9]*)',
        r'expense[=:\s]+([0-9]+[.,]?[0-9]*)',
        r'себест[=:\s]+([0-9]+[.,]?[0-9]*)',  # оставляем для совместимости
        r'cost[=:\s]+([0-9]+[.,]?[0-9]*)'
    ]
    for pattern in cost_patterns:
        match = re.search(pattern, text_lower)
        if match:
            cost = float(match.group(1).replace(',', '.'))
            break
    
    return quantity, unit_price, cost


@router.message(TransactionStates.waiting_for_operation_amount)
async def process_operation_amount(message: Message, state: FSMContext):
    """Обработка введенной суммы для операции"""
    text = message.text.strip()
    
    # Парсинг основной суммы (первое число в тексте)
    numbers = re.findall(r'\d+[.,]?\d*', text)
    if not numbers:
        await message.answer("❌ Неверный формат суммы. Введите число, например: 1000 или 500.50")
        return
    
    try:
        amount = float(numbers[0].replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Попробуйте еще раз.")
            return
    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число, например: 1000 или 500.50")
        return
    
    # Парсинг юнит-данных
    quantity, unit_price, cost = parse_unit_data(text)
    
    # Если указано количество и цена, пересчитываем сумму
    if quantity and unit_price:
        amount = quantity * unit_price
    
    data = await state.get_data()
    operation_type = data.get("operation")
    payment_type = data.get("payment_type")
    category_id = data.get("category_id")
    
    # Расходы учитываются только при вычитании
    expenses = cost if operation_type == "subtract" else None
    
    await db.add_transaction(
        chat_id=message.chat.id,
        amount=amount,
        payment_type=payment_type,
        operation_type=operation_type,
        description=f"Операция от {message.from_user.first_name}",
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.first_name,
        category_id=category_id,
        quantity=quantity,
        unit_price=unit_price,
        cost=expenses
    )
    
    payment_name = "наличными" if payment_type == "cash" else "безналичными"
    operation_name = "добавлено" if operation_type == "add" else "вычтено"
    
    response = f"✅ {operation_name.capitalize()} {amount:.2f} ₽ {payment_name}"
    if quantity:
        response += f"\nКоличество: {quantity:.1f} ед."
    if unit_price:
        response += f"\nЦена за единицу: {unit_price:.2f} ₽"
    if expenses:
        response += f"\nРасходы: {expenses:.2f} ₽"
    
    await message.answer(response, reply_markup=get_main_keyboard())
    
    # Показываем обновленный баланс
    await show_balance(message.chat.id, message)
    
    await state.clear()


@router.message(TransactionStates.waiting_for_amount)
async def process_transaction(message: Message, state: FSMContext):
    """Обработка введенной суммы (старый формат)"""
    amount, payment_type = parse_amount(message.text)
    
    if amount is None:
        await message.answer("❌ Не удалось распознать сумму. Попробуйте еще раз.")
        return
    
    if payment_type is None:
        await message.answer(
            "❌ Не указан тип оплаты. Укажите 'нал' или 'карт'\n"
            "Например: 1000 нал"
        )
        return
    
    operation_type = "add" if amount > 0 else "subtract"
    amount = abs(amount)
    
    await db.add_transaction(
        chat_id=message.chat.id,
        amount=amount,
        payment_type=payment_type,
        operation_type=operation_type,
        description=f"Операция от {message.from_user.first_name}",
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.first_name
    )
    
    payment_name = "наличными" if payment_type == "cash" else "безналичными"
    operation_name = "добавлено" if operation_type == "add" else "вычтено"
    
    await message.answer(
        f"✅ {operation_name.capitalize()} {amount:.2f} ₽ {payment_name}",
        reply_markup=get_main_keyboard()
    )
    
    # Показываем обновленный баланс
    await show_balance(message.chat.id, message)
    
    await state.clear()


@router.message(TransactionStates.waiting_for_category_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    # Игнорируем команды
    if message.text and message.text.startswith('/'):
        return
    
    if not message.text:
        await message.answer("❌ Пожалуйста, введите текстовое название категории.")
        return
    
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым. Попробуйте еще раз.")
        return
        
    if len(category_name) > 50:
        await message.answer("❌ Название категории слишком длинное (макс. 50 символов). Попробуйте еще раз.")
        return
    
    # Получаем тип категории из состояния
    data = await state.get_data()
    category_type = data.get("category_type", "income_source")
    
    category_id = await db.create_category(message.chat.id, category_name, category_type)
    if category_id:
        type_text = "источник дохода" if category_type == "income_source" else "категория расхода"
        await message.answer(
            f"✅ {type_text.capitalize()} '{category_name}' создан(а)!",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"❌ Категория '{category_name}' уже существует.",
            reply_markup=get_main_keyboard()
        )
    await state.clear()


@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext):
    """Обработка текстовых сообщений с суммами"""
    # Пропускаем команды
    if message.text.startswith('/'):
        return
    
    # Пропускаем, если ожидается ввод категории или других специальных данных
    current_state = await state.get_state()
    if current_state in [
        TransactionStates.waiting_for_category_name,
        TransactionStates.waiting_for_operation_amount,
        TransactionStates.waiting_for_payment_type
    ]:
        return
    
    amount, payment_type = parse_amount(message.text)
    
    # Если распознана сумма и тип оплаты, обрабатываем транзакцию
    if amount is not None and payment_type is not None:
        operation_type = "add" if amount > 0 else "subtract"
        amount = abs(amount)
        
        await db.add_transaction(
            chat_id=message.chat.id,
            amount=amount,
            payment_type=payment_type,
            operation_type=operation_type,
            description=message.text,
            user_id=message.from_user.id,
            username=message.from_user.username or message.from_user.first_name
        )
        
        payment_name = "наличными" if payment_type == "cash" else "безналичными"
        operation_name = "добавлено" if operation_type == "add" else "вычтено"
        
        if message.chat.type == 'private':
            await message.answer(
                f"✅ {operation_name.capitalize()} {amount:.2f} ₽ {payment_name}",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.reply(
                f"✅ {operation_name.capitalize()} {amount:.2f} ₽ {payment_name}"
            )
        
        # Показываем обновленный баланс
        await show_balance(message.chat.id, message)
    else:
        # Если сообщение не распознано, показываем подсказку в личных чатах
        if message.chat.type == 'private':
            await message.answer(
                "❓ Не удалось распознать операцию.\n\n"
                "Используйте кнопки ниже или отправьте сообщение в формате:\n"
                "• 1000 нал - добавить 1000 наличными\n"
                "• +500 карт - добавить 500 безналичными\n"
                "• -200 нал - вычесть 200 наличными",
                reply_markup=get_main_keyboard()
            )


# Обработчики callback-запросов от кнопок
@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "💰 Бот для подсчета кассы с юнит-экономикой\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям.\n\n"
        "Быстрый ввод сумм:\n"
        "+1000 нал - добавить 1000 наличными\n"
        "-500 карт - вычесть 500 с карты\n"
        "2000 нал - добавить 2000 наличными\n\n"
        "Юнит-экономика:\n"
        "• Создавайте категории для организации транзакций\n"
        "• Указывайте количество и цену: 500 кол 5 цена 100\n"
        "• Отслеживайте прибыльность по категориям",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "balance")
async def callback_balance(callback: CallbackQuery):
    """Обработка нажатия кнопки баланса"""
    await show_balance(callback.message.chat.id, callback)


@router.callback_query(F.data == "history")
async def callback_history(callback: CallbackQuery):
    """Обработка нажатия кнопки истории"""
    await show_history(callback.message.chat.id, callback)


@router.callback_query(F.data == "refresh")
async def callback_refresh(callback: CallbackQuery):
    """Обновление главного меню"""
    await callback_main_menu(callback)


@router.callback_query(F.data == "add_menu")
async def callback_add_menu(callback: CallbackQuery, state: FSMContext):
    """Меню добавления средств"""
    await state.update_data(operation="add")
    await callback.message.edit_text(
        "➕ Добавление средств\n\nВыберите тип оплаты:",
        reply_markup=get_payment_type_keyboard("add")
    )
    await state.set_state(TransactionStates.waiting_for_payment_type)
    await callback.answer()


@router.callback_query(F.data == "subtract_menu")
async def callback_subtract_menu(callback: CallbackQuery, state: FSMContext):
    """Меню вычитания средств"""
    await state.update_data(operation="subtract")
    await callback.message.edit_text(
        "➖ Вычитание средств\n\nВыберите тип оплаты:",
        reply_markup=get_payment_type_keyboard("subtract")
    )
    await state.set_state(TransactionStates.waiting_for_payment_type)
    await callback.answer()


@router.callback_query(F.data.in_(["add_cash", "add_card", "subtract_cash", "subtract_card"]))
async def callback_payment_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа оплаты"""
    data = callback.data.split("_")
    operation = data[0]
    payment_type = data[1]
    
    await state.update_data(operation=operation, payment_type=payment_type)
    
    operation_text = "добавления" if operation == "add" else "вычитания"
    payment_text = "наличными" if payment_type == "cash" else "безналичными"
    
    # При добавлении - выбор источника дохода, при вычитании - категории расхода
    if operation == "add":
        categories = await db.get_income_sources(callback.message.chat.id)
        category_type_text = "источник дохода"
    else:
        categories = await db.get_expense_categories(callback.message.chat.id)
        category_type_text = "категорию расхода"
    
    if categories:
        keyboard_buttons = []
        for cat_id, name, description, cat_type, created_at in categories:
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"📁 {name}", callback_data=f"select_cat_{cat_id}")
            ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_category")
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"Выберите {category_type_text} для {operation_text} {payment_text}:\n\n"
            f"Или пропустите, если не нужно.",
            reply_markup=keyboard
        )
        await state.set_state(TransactionStates.waiting_for_category)
    else:
        hint = get_unit_economics_hint(operation)
        await callback.message.edit_text(
            f"Введите сумму для {operation_text} {payment_text}:\n\n"
            f"Например: 1000 или 500.50\n\n"
            f"{hint}"
        )
        await state.set_state(TransactionStates.waiting_for_operation_amount)
    
    await callback.answer()


@router.callback_query(F.data.startswith("select_cat_"))
async def callback_select_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории для транзакции"""
    category_id = int(callback.data.split("_")[-1])
    await state.update_data(category_id=category_id)
    
    categories = await db.get_categories(callback.message.chat.id)
    category = next((c for c in categories if c[0] == category_id), None)
    category_name = category[1] if category else "Неизвестная"
    
    data = await state.get_data()
    operation = data.get("operation")
    payment_type = data.get("payment_type")
    
    operation_text = "добавления" if operation == "add" else "вычитания"
    payment_text = "наличными" if payment_type == "cash" else "безналичными"
    
    hint = get_unit_economics_hint(operation)
    await callback.message.edit_text(
        f"Категория: {category_name}\n\n"
        f"Введите сумму для {operation_text} {payment_text}:\n\n"
        f"Например: 1000 или 500.50\n\n"
        f"{hint}"
    )
    await state.set_state(TransactionStates.waiting_for_operation_amount)
    await callback.answer()


@router.callback_query(F.data == "skip_category")
async def callback_skip_category(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора категории"""
    data = await state.get_data()
    operation = data.get("operation")
    payment_type = data.get("payment_type")
    
    operation_text = "добавления" if operation == "add" else "вычитания"
    payment_text = "наличными" if payment_type == "cash" else "безналичными"
    
    hint = get_unit_economics_hint(operation)
    await callback.message.edit_text(
        f"Введите сумму для {operation_text} {payment_text}:\n\n"
        f"Например: 1000 или 500.50\n\n"
        f"{hint}"
    )
    await state.set_state(TransactionStates.waiting_for_operation_amount)
    await callback.answer()


# Обработчики для категорий
@router.callback_query(F.data == "categories_menu")
async def callback_categories_menu(callback: CallbackQuery):
    """Меню управления категориями"""
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="💰 Источники дохода", callback_data="income_sources_menu")
        ],
        [
            InlineKeyboardButton(text="💸 Категории расходов", callback_data="expense_categories_menu")
        ],
        [
            InlineKeyboardButton(text="📊 Сводная таблица", callback_data="summary_table")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = (
        "📁 Управление категориями\n\n"
        "• Источники дохода - для учета доходов (Авито, сайт, сарафан и т.д.)\n"
        "• Категории расходов - для учета расходов по категориям\n"
        "• Сводная таблица - статистика доходов и расходов"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "income_sources_menu")
async def callback_income_sources_menu(callback: CallbackQuery):
    """Меню источников дохода"""
    sources = await db.get_income_sources(callback.message.chat.id)
    
    keyboard_buttons = []
    for cat_id, name, description, cat_type, created_at in sources:
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"💰 {name}", callback_data=f"cat_view_{cat_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_cat_{cat_id}")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="➕ Добавить источник", callback_data="create_income_source")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="categories_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = "💰 Источники дохода:\n\n"
    if sources:
        for cat_id, name, description, cat_type, created_at in sources:
            text += f"• {name}"
            if description:
                text += f" - {description}"
            text += "\n"
    else:
        text += "Источники дохода не созданы.\n"
        text += "Примеры: Авито, Сайт, Сарафан, Приложение"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "expense_categories_menu")
async def callback_expense_categories_menu(callback: CallbackQuery):
    """Меню категорий расходов"""
    categories = await db.get_expense_categories(callback.message.chat.id)
    
    keyboard_buttons = []
    for cat_id, name, description, cat_type, created_at in categories:
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"💸 {name}", callback_data=f"cat_view_{cat_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_cat_{cat_id}")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="➕ Добавить категорию", callback_data="create_expense_category")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="categories_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = "💸 Категории расходов:\n\n"
    if categories:
        for cat_id, name, description, cat_type, created_at in categories:
            text += f"• {name}"
            if description:
                text += f" - {description}"
            text += "\n"
    else:
        text += "Категории расходов не созданы.\n"
        text += "Примеры: Закупка, Реклама, Аренда, Зарплата"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "create_income_source")
async def callback_create_income_source(callback: CallbackQuery, state: FSMContext):
    """Создание источника дохода"""
    await state.update_data(category_type="income_source")
    await callback.message.edit_text(
        "➕ Создание источника дохода\n\n"
        "Введите название источника:\n"
        "Например: Авито, Сайт, Сарафан, Приложение"
    )
    await state.set_state(TransactionStates.waiting_for_category_name)
    await callback.answer()


@router.callback_query(F.data == "create_expense_category")
async def callback_create_expense_category(callback: CallbackQuery, state: FSMContext):
    """Создание категории расхода"""
    await state.update_data(category_type="expense_category")
    await callback.message.edit_text(
        "➕ Создание категории расхода\n\n"
        "Введите название категории:\n"
        "Например: Закупка, Реклама, Аренда, Зарплата"
    )
    await state.set_state(TransactionStates.waiting_for_category_name)
    await callback.answer()


@router.callback_query(F.data == "cat_create")
async def callback_category_create(callback: CallbackQuery, state: FSMContext):
    """Создание новой категории"""
    await callback.message.edit_text(
        "➕ Создание категории\n\n"
        "Введите название категории:\n"
        "Например: Кофе, Обеды, Товары"
    )
    await state.set_state(TransactionStates.waiting_for_category_name)
    await callback.answer()


@router.callback_query(F.data.startswith("cat_view_"))
async def callback_category_view(callback: CallbackQuery):
    """Просмотр категории"""
    category_id = int(callback.data.split("_")[-1])
    categories = await db.get_categories(callback.message.chat.id)
    category = next((c for c in categories if c[0] == category_id), None)
    
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    cat_id, name, description, cat_type, created_at = category
    
    # Получаем статистику по категории
    stats = await db.get_unit_economics_by_category(callback.message.chat.id, category_id, 30)
    
    category_type_text = "Источник дохода" if cat_type == "income_source" else "Категория расхода"
    back_menu = "income_sources_menu" if cat_type == "income_source" else "expense_categories_menu"
    
    text = f"📁 {category_type_text}: {name}\n"
    if description:
        text += f"Описание: {description}\n"
    text += f"\n📊 Статистика за 30 дней:\n\n"
    
    if stats:
        for row in stats:
            cat_id, cat_name, trans_count, quantity, avg_price, revenue, cost, avg_amount = row
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            text += (
                f"Транзакций: {trans_count}\n"
                f"Единиц продано: {quantity:.1f}\n"
                f"Выручка: {revenue:.2f} ₽\n"
                f"Расходы: {cost:.2f} ₽\n"
                f"Прибыль: {profit:.2f} ₽\n"
                f"Маржа: {margin:.1f}%\n"
                f"Средний чек: {avg_amount:.2f} ₽\n"
                f"Средняя цена за единицу: {avg_price:.2f} ₽\n"
            )
    else:
        text += "Нет данных за этот период"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_cat_{category_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=back_menu)
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("delete_cat_"))
async def callback_delete_category(callback: CallbackQuery):
    """Подтверждение удаления категории"""
    category_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о категории
    categories = await db.get_categories(callback.message.chat.id)
    category = next((c for c in categories if c[0] == category_id), None)
    
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    cat_id, name, description, cat_type, created_at = category
    category_type_text = "источник дохода" if cat_type == "income_source" else "категорию расхода"
    back_menu = "income_sources_menu" if cat_type == "income_source" else "expense_categories_menu"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{category_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cat_view_{category_id}")
        ]
    ])
    
    await callback.message.edit_text(
        f"⚠️ Подтвердите удаление\n\n"
        f"Вы уверены, что хотите удалить {category_type_text} '{name}'?\n\n"
        f"Все транзакции, связанные с этой категорией, останутся, но категория будет удалена.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def callback_confirm_delete(callback: CallbackQuery):
    """Подтвержденное удаление категории"""
    category_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о категории для возврата в правильное меню (до удаления)
    categories = await db.get_categories(callback.message.chat.id)
    category = next((c for c in categories if c[0] == category_id), None)
    
    if not category:
        # Категория уже удалена, возвращаемся в общее меню категорий
        await callback.answer("❌ Категория не найдена (возможно, уже удалена)", show_alert=True)
        fake_callback = type('obj', (object,), {
            'message': callback.message,
            'answer': lambda x: None,
            'data': 'categories_menu'
        })()
        await callback_categories_menu(fake_callback)
        return
    
    cat_id, name, description, cat_type, created_at = category
    category_type_text = "источник дохода" if cat_type == "income_source" else "категория расхода"
    back_menu = "income_sources_menu" if cat_type == "income_source" else "expense_categories_menu"
    
    # Удаляем категорию
    await db.delete_category(callback.message.chat.id, category_id)
    
    # Удаляем категорию
    await db.delete_category(callback.message.chat.id, category_id)
    
    await callback.answer(f"✅ {category_type_text.capitalize()} '{name}' удален(а)", show_alert=True)
    
    # Возвращаемся в соответствующее меню, создав новый callback
    fake_callback = type('obj', (object,), {
        'message': callback.message,
        'answer': lambda x: None,
        'data': back_menu
    })()
    
    if cat_type == "income_source":
        await callback_income_sources_menu(fake_callback)
    else:
        await callback_expense_categories_menu(fake_callback)


@router.callback_query(F.data == "summary_table")
async def callback_summary_table(callback: CallbackQuery):
    """Сводная таблица доходов и расходов по категориям с процентами"""
    summary = await db.get_summary_by_categories(callback.message.chat.id, 30)
    
    text = f"📊 Сводная таблица за {summary['days']} дней\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Доходы по источникам
    text += "💰 ДОХОДЫ:\n"
    if summary['incomes']:
        total_income = summary['total_income'] or 1  # Избегаем деления на ноль
        for cat_id, name, income, count in summary['incomes']:
            percentage = (income / total_income * 100) if total_income > 0 else 0
            text += f"• {name}: {income:.2f} ₽ ({percentage:.1f}%)\n"
        text += f"\nИтого доходов: {summary['total_income']:.2f} ₽\n\n"
    else:
        text += "Нет данных\n\n"
    
    # Расходы по категориям
    text += "💸 РАСХОДЫ:\n"
    if summary['expenses']:
        total_expense = summary['total_expense'] or 1
        for cat_id, name, expense, count in summary['expenses']:
            percentage = (expense / total_expense * 100) if total_expense > 0 else 0
            text += f"• {name}: {expense:.2f} ₽ ({percentage:.1f}%)\n"
        text += f"\nИтого расходов: {summary['total_expense']:.2f} ₽\n\n"
    else:
        text += "Нет данных\n\n"
    
    # Итоги
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"💰 Доходы: {summary['total_income']:.2f} ₽\n"
    text += f"💸 Расходы: {summary['total_expense']:.2f} ₽\n"
    profit = summary['total_income'] - summary['total_expense']
    text += f"📈 Прибыль: {profit:.2f} ₽\n"
    
    if summary['total_income'] > 0:
        margin = (profit / summary['total_income'] * 100)
        text += f"📊 Маржа: {margin:.1f}%"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="categories_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# Обработчики для юнит-экономики
@router.callback_query(F.data == "unit_economics")
async def callback_unit_economics(callback: CallbackQuery):
    """Показать юнит-экономику"""
    summary = await db.get_unit_economics_summary(callback.message.chat.id, 30)
    categories_stats = await db.get_unit_economics_by_category(callback.message.chat.id, None, 30)
    
    text = "📊 Юнит-экономика за 30 дней\n\n"
    
    if summary and summary['revenue'] > 0:
        text += (
            f"💰 Общая статистика:\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Транзакций: {summary['transactions']}\n"
            f"Единиц продано: {summary['units_sold']:.1f}\n"
            f"Выручка: {summary['revenue']:.2f} ₽\n"
            f"Расходы: {summary['cost']:.2f} ₽\n"
            f"Прибыль: {summary['profit']:.2f} ₽\n"
            f"Маржа: {summary['margin']:.1f}%\n"
            f"Средний чек: {summary['avg_check']:.2f} ₽\n"
            f"Средняя цена за единицу: {summary['avg_unit_price']:.2f} ₽\n\n"
        )
    else:
        text += "💰 Общая статистика:\nНет данных за этот период\n\n"
    
    if categories_stats:
        text += "📁 По категориям:\n━━━━━━━━━━━━━━━━━━━━\n"
        for row in categories_stats[:5]:  # Показываем топ-5
            cat_id, cat_name, trans_count, quantity, avg_price, revenue, cost, avg_amount = row
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            cat_name_display = cat_name if cat_name else "Без категории"
            text += (
                f"\n{cat_name_display}:\n"
                f"  Выручка: {revenue:.2f} ₽\n"
                f"  Прибыль: {profit:.2f} ₽ ({margin:.1f}%)\n"
                f"  Единиц: {quantity:.1f}\n"
            )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 По категориям", callback_data="categories_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(Command("unit"))
async def cmd_unit(message: Message):
    """Команда для просмотра юнит-экономики"""
    callback = type('obj', (object,), {
        'message': message,
        'answer': lambda x: None,
        'data': 'unit_economics'
    })()
    await callback_unit_economics(callback)


@router.message(Command("categories"))
async def cmd_categories(message: Message):
    """Команда для просмотра категорий"""
    callback = type('obj', (object,), {
        'message': message,
        'answer': lambda x: None,
        'data': 'categories_menu'
    })()
    await callback_categories_menu(callback)

