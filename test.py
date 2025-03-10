import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

BOT_TOKEN = " "

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище для активных напоминаний
reminders = {}

class ReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-напоминалка.\n"
        "Чтобы установить напоминание используй /set"
    )


@dp.message(Command("set"))
async def cmd_set(message: Message, state: FSMContext):
    await message.answer("Введите текст напоминания:")
    await state.set_state(ReminderStates.waiting_for_text)

@dp.message(ReminderStates.waiting_for_text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        "Введите время напоминания в формате:\n"
        "ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Например: 31.12.2024 23:59"
    )
    await state.set_state(ReminderStates.waiting_for_time)

@dp.message(ReminderStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    try:
        reminder_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        if reminder_time < datetime.now():
            await message.answer("Время должно быть в будущем! Попробуйте снова:")
            return

        data = await state.get_data()
        await state.clear()
        
        user_id = message.from_user.id
        reminder_text = data['text']
        
        # Создаем задачу для напоминания
        delay = (reminder_time - datetime.now()).total_seconds()
        task = asyncio.create_task(
            send_reminder(user_id, reminder_text, delay))
        
        # Сохраняем задачу
        if user_id not in reminders:
            reminders[user_id] = []
        reminders[user_id].append(task)
        
        await message.answer(
            f"Напоминание установлено на {reminder_time.strftime('%d.%m.%Y %H:%M')}")

    except ValueError:
        await message.answer("Неверный формат времени! Попробуйте снова:")

async def send_reminder(user_id: int, text: str, delay: float):
    try:
        await asyncio.sleep(delay)
        await bot.send_message(user_id, f"⏰ Напоминание: {text}")
        
        # Удаляем завершенную задачу из хранилища
        if user_id in reminders:
            reminders[user_id] = [task for task in reminders[user_id] if not task.done()]
            
    except Exception as e:
        print(f"Ошибка при отправке напоминания: {e}")

@dp.message(Command("list"))
async def cmd_list(message: Message):
    user_id = message.from_user.id
    if user_id in reminders and len(reminders[user_id]) > 0:
        count = len(reminders[user_id])
        await message.answer(f"У вас {count} активных напоминаний")
    else:
        await message.answer("У вас нет активных напоминаний")

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действие отменено")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())