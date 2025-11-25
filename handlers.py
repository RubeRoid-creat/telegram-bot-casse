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
            InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
        ]
    ])
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    await message.answer(
        "💰 Бот для подсчета кассы\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям.\n\n"
        "Также можно писать суммы в чат:\n"
        "+1000 нал - добавить 1000 наличными\n"
        "-500 карт - вычесть 500 с карты\n"
        "2000 нал - добавить 2000 наличными",
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


@router.message(TransactionStates.waiting_for_operation_amount)
async def process_operation_amount(message: Message, state: FSMContext):
    """Обработка введенной суммы для операции"""
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Попробуйте еще раз.")
            return
    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число, например: 1000 или 500.50")
        return
    
    data = await state.get_data()
    operation_type = data.get("operation")
    payment_type = data.get("payment_type")
    
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


@router.message(F.text)
async def handle_text_message(message: Message):
    """Обработка текстовых сообщений с суммами"""
    # Пропускаем команды
    if message.text.startswith('/'):
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
        "💰 Бот для подсчета кассы\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям.\n\n"
        "Также можно писать суммы в чат:\n"
        "+1000 нал - добавить 1000 наличными\n"
        "-500 карт - вычесть 500 с карты\n"
        "2000 нал - добавить 2000 наличными",
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
    
    await callback.message.edit_text(
        f"Введите сумму для {operation_text} {payment_text}:\n\n"
        f"Например: 1000 или 500.50"
    )
    await state.set_state(TransactionStates.waiting_for_operation_amount)
    await callback.answer()

