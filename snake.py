import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = ""  # Вставь сюда свой токен
bot = Bot(token=TOKEN)
dp = Dispatcher()  # В aiogram 3.x Dispatcher создается без аргументов
router = Router()
dp.include_router(router)  # Подключаем роутер к диспетчеру

# Размер игрового поля
GRID_SIZE = 10

# Направления движения змейки
directions = {
    "⬆": (-1, 0),
    "⬇": (1, 0),
    "⬅": (0, -1),
    "➡": (0, 1)
}

game_data = {}

async def start_game(chat_id):
    """Инициализация новой игры."""
    snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
    food = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
    direction = "⬆"
    game_data[chat_id] = {"snake": snake, "food": food, "direction": direction}
    await update_game_message(chat_id)

async def update_game_message(chat_id):
    """Обновление игрового поля."""
    data = game_data[chat_id]
    snake = data["snake"]
    food = data["food"]
    
    grid = [["⬜" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for x, y in snake:
        grid[x][y] = "🟩"
    grid[food[0]][food[1]] = "🍎"

    field = "\n".join("".join(row) for row in grid)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆", callback_data="move_⬆")],
        [InlineKeyboardButton(text="⬅", callback_data="move_⬅"),
         InlineKeyboardButton(text="➡", callback_data="move_➡")],
        [InlineKeyboardButton(text="⬇", callback_data="move_⬇")]
    ])
    
    await bot.send_message(chat_id, field, reply_markup=keyboard)

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Это змейка в Telegram. Используй кнопки для управления.")
    await start_game(message.chat.id)

@router.callback_query(lambda c: c.data.startswith("move_"))
async def move_snake(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id not in game_data:
        await start_game(chat_id)
        return
    
    new_direction = callback_query.data.split("_")[1]
    data = game_data[chat_id]
    current_direction = data["direction"]

    # Запрещаем движение в противоположном направлении
    if (new_direction == "⬆" and current_direction == "⬇") or \
       (new_direction == "⬇" and current_direction == "⬆") or \
       (new_direction == "⬅" and current_direction == "➡") or \
       (new_direction == "➡" and current_direction == "⬅"):
        return
    
    data["direction"] = new_direction
    await move_snake_logic(chat_id)
    await update_game_message(chat_id)

async def move_snake_logic(chat_id):
    """Обновляет положение змейки."""
    data = game_data[chat_id]
    snake = data["snake"]
    direction = data["direction"]
    food = data["food"]
    
    head_x, head_y = snake[-1]
    move_x, move_y = directions[direction]
    new_head = (head_x + move_x, head_y + move_y)
    
    # Проверка столкновения со стенами или собой
    if new_head in snake or not (0 <= new_head[0] < GRID_SIZE and 0 <= new_head[1] < GRID_SIZE):
        await bot.send_message(chat_id, "Игра окончена! /start для новой игры.")
        del game_data[chat_id]
        return
    
    snake.append(new_head)
    
    # Проверяем, съела ли змейка еду
    if new_head == food:
        data["food"] = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
    else:
        snake.pop(0)  # Удаляем хвост, если не съедена еда

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


