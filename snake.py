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

GRID_SIZE = 10

directions = {
    "⬆": (-1, 0),
    "⬇": (1, 0),
    "⬅": (0, -1),
    "➡": (0, 1)
}

class SnakeGame:
    def __init__(self):
        self.snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
        self.food = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
        self.direction = "⬆"
    
    def move_snake(self):
        head_x, head_y = self.snake[-1]
        move_x, move_y = directions[self.direction]
        new_head = (head_x + move_x, head_y + move_y)

        # Проверка столкновения со стенами
        if not (0 <= new_head[0] < GRID_SIZE and 0 <= new_head[1] < GRID_SIZE):
           return False
        
        # Проверка столкновения со змеей (только если змея не ест еду)
        if new_head in self.snake and new_head != self.food:
            return False
        
        self.snake.append(new_head)
        
        # Проверяем, съела ли змейка еду
        if new_head == self.food:
            self.food = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
        else:
             self.snake.pop(0)
        return True
        

    def get_grid_representation(self):
       grid = [["⬜" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
       for x, y in self.snake:
           grid[x][y] = "🟩"
       grid[self.food[0]][self.food[1]] = "🍎"
       return "\n".join("".join(row) for row in grid)
    
    def get_score(self):
        return len(self.snake) - 1

game_data = {}

async def update_game_message(chat_id):
    try:
        game = game_data[chat_id]
        field = game.get_grid_representation()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆", callback_data="move_⬆")],
            [InlineKeyboardButton(text="⬅", callback_data="move_⬅"),
             InlineKeyboardButton(text="➡", callback_data="move_➡")],
            [InlineKeyboardButton(text="⬇", callback_data="move_⬇")]
        ])
        await bot.send_message(chat_id, field, reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error updating game message: {e}")

greetings = ["Здравствуй, странник!", "Приготовься к игре!", "Змеиная лихорадка начинается!", "Добро пожаловать в мир пиксельной змеи!", "Привет! Испытай свою ловкость."]

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    name = message.from_user.first_name if message.from_user.first_name else "странник"
    await message.answer(f"{random.choice(greetings)}, {name}! 🐍\nПостарайся прокормить змейку и не врезаться в саму себя! Используй кнопки для управления.")
    game_data[message.chat.id] = SnakeGame()
    await update_game_message(message.chat.id)


@router.callback_query(lambda c: c.data.startswith("move_"))
async def move_snake(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id not in game_data:
        await bot.send_message(chat_id, "Игра ещё не начата! Начни новую игру командой /start")
        return
    
    new_direction = callback_query.data.split("_")[1]
    game = game_data[chat_id]

    # Запрещаем движение в противоположном направлении
    if (new_direction == "⬆" and game.direction == "⬇") or \
        (new_direction == "⬇" and game.direction == "⬆") or \
        (new_direction == "⬅" and game.direction == "➡") or \
        (new_direction == "➡" and game.direction == "⬅"):
        await bot.send_message(chat_id, "Так не получится! 🚫 Змея не может двигаться в обратном направлении.")
        return
    
    game.direction = new_direction
    if not game.move_snake():
      score = game.get_score()
      await bot.send_message(chat_id, f"Игра окончена! ☠️ Змея врезалась в себя, либо в стену. Твой результат: {score}.\n/start для новой игры.")
      del game_data[chat_id]
      return
      
    await update_game_message(chat_id)
    

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
