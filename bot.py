import telebot
import requests
import random
from collections import defaultdict

bot = telebot.TeleBot('7627109915:AAGw5hTJVOlBasDFGJBj_lyPye66rshZrg4')
MY_CHAT_ID = 6707920884
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

user_states = {}
battle_scores = {}
rhyme_game = {}
leaderboard_battle = defaultdict(lambda: {"wins": 0, "games": 0})
leaderboard_rhyme = defaultdict(lambda: {"longest_rounds": 0})

# Список моделей (13 ИИ)
MODELS = [
    "openai/gpt-3.5-turbo",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mixtral-8x7b-instruct",
    "google/gemma-2-9b-it",
    "gryphe/mythomax-l2-13b",
    "meta-llama/llama-3-8b-instruct",
    "openai/gpt-4o-mini",
    "mistralai/mistral-7b-instruct",
    "cohere/command-r-plus",
    "qwen/qwen-2-7b-instruct",
    "facebook/xglm-4.5b",
    "togethercomputer/redpajama-incite-7b-instruct",
    "huggingfaceh4/zephyr-7b-beta",
    "openchat/openchat-3.5-1210",
    "neversleep/noromaid-20b"
]

# Клавиатуры
start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = telebot.types.KeyboardButton("🎤 Реп-баттл")
btn2 = telebot.types.KeyboardButton("🎵 Игра в рифму")
btn3 = telebot.types.KeyboardButton("🏆 Лидерборд")
btn4 = telebot.types.KeyboardButton("Сайт")
btn5 = telebot.types.KeyboardButton("Связь")
start_markup.add(btn1, btn2, btn3, btn4, btn5)

game_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_back = telebot.types.KeyboardButton("🔙 Назад")
game_menu.add(btn_back)


# Генерация реперского стиха для баттла (без стилей)
def generate_poem(round_num=1):
    results = []
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}

    for model in MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system",
                 "content": "Ты репер. Пиши только на русском языке. Составь ровно 4 строки с четким ритмом и звучной рифмой (1-3, 2-4 или 1-4, 2-3). Без лишних слов."},
                {"role": "user", "content": f"Напиши 4-строчный реп, раунд {round_num}."}
            ],
            "max_tokens": 150,
            "temperature": 0.8
        }
        try:
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            poem = response.json()["choices"][0]["message"]["content"].strip()
            lines = poem.split("\n")
            while len(lines) < 4:
                lines.append("...")
            results.append(f"[{model}]:\n" + "\n".join(lines[:4]))
        except requests.exceptions.RequestException as e:
            results.append(f"[{model}]: Ошибка: {str(e)}")
    return "\n\n".join(results)


# Оценка стиха (gpt-3.5-turbo для стабильности)
def evaluate_poem(poem, is_user=False):
    prompt = f"Оцени этот 4-строчный реп по шкале 1-10. Учитывай ритм, четкость рифмы и качество текста. Если рифмы нет или текст короче 4 строк, снижай оценку. Верни только число.\n\n{poem}"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system",
             "content": "Ты критик репа. Оценивай строго: ритм, рифма и качество — ключевые факторы. Верни только число от 1 до 10."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 10,
        "temperature": 0.5
    }
    try:
        response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        score = response.json()["choices"][0]["message"]["content"].strip()
        return int(score) if score.isdigit() and 1 <= int(score) <= 10 else 5
    except requests.exceptions.RequestException as e:
        return f"Ошибка оценки: {str(e)}"


# Генерация рифмы для второй игры (строгая рифма, без повтора слова)
def generate_rhyme(user_line):
    results = []
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}

    for model in MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system",
                 "content": "Ты репер. Пиши только на русском языке. Продолжай строку пользователя одной полноценной строкой, строго рифмуя последнее слово с последним словом строки пользователя. Не повторяй последнее слово строки пользователя в своей строке. Рифма должна быть в конце строки. Пример: если строка 'Я иду домой', ответ должен быть вроде 'Встречу вечер золотой', рифмуя 'домой' с 'золотой', но не 'Я пришёл домой'. Не пиши просто слова, только полную строку. Без лишних слов."},
                {"role": "user",
                 "content": f"Продолжи одной полноценной строкой, зарифмуй последнее слово строки '{user_line}'."}
            ],
            "max_tokens": 50,
            "temperature": 0.8
        }
        try:
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            rhyme = response.json()["choices"][0]["message"]["content"].strip()
            results.append(f"[{model}]: {rhyme}")
        except requests.exceptions.RequestException as e:
            results.append(f"[{model}]: Ошибка: {str(e)}")
    return "\n".join(results)


@bot.message_handler(commands=['start'])
def main(message):
    user_states[message.chat.id] = None
    bot.send_message(message.chat.id, (
        "🎤 Привет! Это реп-арена.\n"
        "Реп-баттл: до 2 побед, max 3 раунда (13 ИИ генерируют).\n"
        "Игра в рифму: кидай строку, 13 ИИ зарифмуют.\n"
        "Выбирай игру!"
    ), reply_markup=start_markup)


@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle_message(message):
    chat_id = message.chat.id
    username = message.from_user.username or str(chat_id)

    if message.text == "🎤 Реп-баттл":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "Раунд 1. Читай реп (4 строки)!", reply_markup=game_menu)
        user_states[chat_id] = {"state": "battle", "round": 1, "user_wins": 0, "rival_wins": 0}
        battle_scores[chat_id] = []

    elif message.text == "🎵 Игра в рифму":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "Кидай строку, тринадцать ИИ зарифмуют!", reply_markup=game_menu)
        user_states[chat_id] = {"state": "rhyme_game", "rounds": 0}

    elif message.text == "🏆 Лидерборд":
        top_battle = sorted(leaderboard_battle.items(),
                            key=lambda x: x[1]["wins"] / x[1]["games"] if x[1]["games"] else 0, reverse=True)[:10]
        top_rhyme = sorted(leaderboard_rhyme.items(), key=lambda x: x[1]["longest_rounds"], reverse=True)[:10]
        bot.send_message(chat_id, (
                "🏆 Топ-10 Реп-баттл:\n" + "\n".join(
            f"@{u}: {d['wins']}/{d['games']} ({d['wins'] / d['games'] * 100:.1f}%)"
            for u, d in top_battle
        ) + "\n\n🏆 Топ-10 Игра в рифму:\n" + "\n".join(
            f"@{u}: {d['longest_rounds']} раундов"
            for u, d in top_rhyme
        )
        ))

    elif message.text == "Сайт":
        bot.send_message(chat_id,
                         "Ссылка: https://itvdn.blob.core.windows.net/cbs-images/cbs-images-a7e0d809-f232-4073-a035-0c7083421dde.PNG")

    elif message.text == "Связь":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "Пиши или кидай фото/видео:")
        user_states[chat_id] = "awaiting_feedback"

    elif message.text == "🔙 Назад":
        user_states[chat_id] = None
        bot.send_message(chat_id, "Выбирай игру!", reply_markup=start_markup)

    elif chat_id in user_states and isinstance(user_states[chat_id], dict):
        state = user_states[chat_id]["state"]

        if state == "battle" and message.text:
            round_num = user_states[chat_id]["round"]
            user_poem = message.text
            rival_poems = generate_poem(round_num)
            bot.send_message(chat_id, f"Раунд {round_num}. Все ИИ сгенерировали:\n\n{rival_poems}")

            # Для оценки используем только первую модель (gpt-3.5-turbo)
            rival_poem = rival_poems.split("\n\n")[0].split("\n", 1)[1]
            user_score = evaluate_poem(user_poem, is_user=True)
            if "Ошибка" in str(user_score):
                bot.send_message(chat_id, user_score)
                return
            rival_score = evaluate_poem(rival_poem)
            if "Ошибка" in str(rival_score):
                bot.send_message(chat_id, rival_score)
                return

            battle_scores[chat_id].append((user_poem, user_score, rival_poem, rival_score))

            winner = "Ты" if user_score > rival_score else "ИИ" if rival_score > user_score else "Ничья"
            bot.send_message(chat_id, f"Раунд {round_num}: {winner} впереди (оценка по gpt-3.5-turbo).")

            if user_score > rival_score:
                user_states[chat_id]["user_wins"] += 1
            elif rival_score > user_score:
                user_states[chat_id]["rival_wins"] += 1

            if user_states[chat_id]["user_wins"] == 2 or user_states[chat_id]["rival_wins"] == 2 or round_num == 3:
                leaderboard_battle[username]["games"] += 1
                if user_states[chat_id]["user_wins"] > user_states[chat_id]["rival_wins"]:
                    leaderboard_battle[username]["wins"] += 1
                    winner_msg = f"Ты победил {user_states[chat_id]['user_wins']}:{user_states[chat_id]['rival_wins']}!"
                elif user_states[chat_id]["rival_wins"] > user_states[chat_id]["user_wins"]:
                    winner_msg = f"ИИ победили {user_states[chat_id]['rival_wins']}:{user_states[chat_id]['user_wins']}."
                else:
                    winner_msg = "Ничья!"

                scores_msg = "\n".join(
                    f"Раунд {i + 1}: Ты - {s[1]}/10, ИИ - {s[3]}/10" for i, s in enumerate(battle_scores[chat_id]))
                bot.send_message(chat_id, f"🎉 Итог:\n{scores_msg}\n{winner_msg}", reply_markup=start_markup)
                user_states[chat_id] = None
                del battle_scores[chat_id]
            else:
                user_states[chat_id]["round"] += 1
                bot.send_message(chat_id, f"Раунд {round_num + 1}. Читай дальше!", reply_markup=game_menu)

        elif state == "rhyme_game" and message.text:
            if message.text.lower() == "стоп":
                rounds = user_states[chat_id]["rounds"]
                if rounds > leaderboard_rhyme[username]["longest_rounds"]:
                    leaderboard_rhyme[username]["longest_rounds"] = rounds
                bot.send_message(chat_id, f"🎵 Игра окончена. Раундов: {rounds}", reply_markup=start_markup)
                user_states[chat_id] = None
            else:
                user_line = message.text
                rival_lines = generate_rhyme(user_line)
                bot.send_message(chat_id, f"Твоя строка: {user_line}\n\n{rival_lines}")
                user_states[chat_id]["rounds"] += 1

    elif chat_id in user_states and user_states[chat_id] == "awaiting_feedback":
        try:
            if message.text:
                bot.send_message(MY_CHAT_ID, f"Связь от @{username}:\n{message.text}")
            elif message.photo:
                bot.forward_message(MY_CHAT_ID, chat_id, message.message_id)
            elif message.video:
                bot.forward_message(MY_CHAT_ID, chat_id, message.message_id)
            bot.send_message(chat_id, "Спасибо за фидбек!", reply_markup=start_markup)
            user_states[chat_id] = None
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка: {str(e)}. Попробуй еще!")

    else:
        bot.send_message(chat_id, "Жми кнопки! /start — для начала.")


bot.polling(none_stop=True)
