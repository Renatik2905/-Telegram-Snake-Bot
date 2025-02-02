import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = "YOUR_BOT_TOKEN"  # Замените на свой токен
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Размер игрового поля и базовые настройки
GRID_SIZE = 10
SPEED = 0.3  # Базовая скорость змейки

# Направления движения змейки
directions = {
    "⬆": (-1, 0),
    "⬇": (1, 0),
    "⬅": (0, -1),
    "➡": (0, 1)
}

game_data = {}

async def start_game(chat_id, difficulty=1):
    """Инициализация новой игры с учётом сложности."""
    # Устанавливаем параметры в зависимости от сложности
    global SPEED
    if difficulty == 1:
        SPEED = 0.3
    elif difficulty == 2:
        SPEED = 0.2
    elif difficulty == 3:
        SPEED = 0.1

    snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
    food = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
    direction = "⬆"
    score = 0  # Очки
    game_data[chat_id] = {"snake": snake, "food": food, "direction": direction, "score": score, "difficulty": difficulty}
    await update_game_message(chat_id)

async def update_game_message(chat_id):
    """Обновление игрового поля и отображение очков."""
    data = game_data[chat_id]
    snake = data["snake"]
    food = data["food"]
    direction = data["direction"]
    score = data["score"]

    # Обновляем игровое поле
    grid = [["⬜" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for x, y in snake:
        grid[x][y] = "🟩"
    grid[food[0]][food[1]] = "🍎"

    field = "\n".join("".join(row) for row in grid)
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⬆", callback_data="move_⬆"),
        InlineKeyboardButton("⬇", callback_data="move_⬇"),
        InlineKeyboardButton("⬅", callback_data="move_⬅"),
        InlineKeyboardButton("➡", callback_data="move_➡")
    )
    
    # Отображаем очки и сложность
    await bot.send_message(chat_id, f"Сложность: {data['difficulty']}\nОчки: {score}\n\n{field}", reply_markup=keyboard)

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """Обработчик команды /start"""
    await message.answer("Привет! Это змейка в Telegram. Используй кнопки для управления. Выберите сложность: 1 - Легко, 2 - Средне, 3 - Сложно.")
    
    # Начинаем игру с легкой сложности
    await start_game(message.chat.id, difficulty=1)

@router.callback_query(lambda c: c.data.startswith("move_"))
async def move_snake(callback_query: types.CallbackQuery):
    """Обработчик движения змейки"""
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
    """Обновляет положение змейки и проверяет столкновения"""
    data = game_data[chat_id]
    snake = data["snake"]
    direction = data["direction"]
    food = data["food"]
    score = data["score"]
    
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
        data["food"] = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))  # Новая еда
        data["score"] += 1  # Увеличиваем очки
        # Увеличиваем сложность по мере роста очков
        if data["score"] % 5 == 0:
            data["difficulty"] += 1
            await start_game(chat_id, difficulty=data["difficulty"])
    else:
        snake.pop(0)  # Удаляем хвост, если не съедена еда

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
