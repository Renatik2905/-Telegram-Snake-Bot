import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = ""  # Замените на свой токен
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Размер игрового поля
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
    # Проверь, существует ли chat_id в game_data
    if chat_id not in game_data:
        await bot.send_message(chat_id, "Игра не началась! Напишите /start.")
        return

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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆", callback_data="move_⬆")],
        [InlineKeyboardButton(text="⬅", callback_data="move_⬅"),
         InlineKeyboardButton(text="➡", callback_data="move_➡")],
        [InlineKeyboardButton(text="⬇", callback_data="move_⬇")]
    ])
    
    # Отображаем очки и сложность
    await bot.send_message(chat_id, f"Сложность: {data['difficulty']}\nОчки: {score}\n\n{field}", reply_markup=keyboard)

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """Обработчик команды /start для выбора уровня сложности"""
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Легко", callback_data="difficulty_1")],
        [InlineKeyboardButton(text="Средне", callback_data="difficulty_2")],
        [InlineKeyboardButton(text="Сложно", callback_data="difficulty_3")]
    ])
    await message.answer("Привет! Это змейка в Telegram. Выберите уровень сложности:", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("difficulty_"))
async def set_difficulty(callback_query: types.CallbackQuery):
    """Обработчик выбора сложности"""
    difficulty = int(callback_query.data.split("_")[1])
    chat_id = callback_query.message.chat.id
    await callback_query.answer()  # Закрываем уведомление о кнопке
    await start_game(chat_id, difficulty)

@router.callback_query(lambda c: c.data.startswith("move_"))
async def move_snake(callback_query: types.CallbackQuery):
    """Обработчик движения змейки"""
    chat_id = callback_query.message.chat.id
    if chat_id not in game_data:  # Проверяем, что игра началась
        await callback_query.answer("Игра ещё не началась! Напишите /start для начала.")
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
        
        # Проверка на достижение 5 очков
        if data["score"] % 5 == 0:
            # Увеличиваем сложность, но не перезапускаем игру
            if data["difficulty"] < 3:  # Максимальная сложность 3
                data["difficulty"] += 1
                await bot.send_message(chat_id, f"Сложность увеличена до {data['difficulty']}!")
    
    else:
        snake.pop(0)  # Удаляем хвост, если не съедена еда


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
