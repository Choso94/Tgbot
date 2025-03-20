import telebot
import requests
from collections import defaultdict

bot = telebot.TeleBot('7627109915:AAGw5hTJVOlBasDFGJBj_lyPye66rshZrg4')
MY_CHAT_ID = 6707920884
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

user_states = {}
battle_scores = {}
profiles = defaultdict(lambda: {"nick": None, "desc": "Нет описания", "avatar": None})
leaderboard_battle = defaultdict(lambda: {"wins": 0, "games": 0})
leaderboard_rhyme = defaultdict(lambda: {"longest_rounds": 0})

# Клавиатуры
start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = telebot.types.KeyboardButton("🎤 Реп-баттл")
btn2 = telebot.types.KeyboardButton("🎵 Игра в рифму")
btn3 = telebot.types.KeyboardButton("🏆 Лидерборд")
btn4 = telebot.types.KeyboardButton("👤 Профиль")
btn5 = telebot.types.KeyboardButton("🌐 Онлайн")
btn6 = telebot.types.KeyboardButton("Сайт")
btn7 = telebot.types.KeyboardButton("Связь")
start_markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)

rivals_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_gogol = telebot.types.KeyboardButton("Гоголь")
btn_pushkin = telebot.types.KeyboardButton("Пушкин")
btn_esenin = telebot.types.KeyboardButton("Есенин")
btn_lermontov = telebot.types.KeyboardButton("Лермонтов")
btn_tolstoy = telebot.types.KeyboardButton("Толстой")
rivals_markup.add(btn_gogol, btn_pushkin, btn_esenin, btn_lermontov, btn_tolstoy)

game_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_back = telebot.types.KeyboardButton("🔙 Назад")
btn_change = telebot.types.KeyboardButton("🔄 Сменить поэта")
game_menu.add(btn_back, btn_change)

profile_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_nick = telebot.types.KeyboardButton("Сменить ник")
btn_desc = telebot.types.KeyboardButton("Сменить описание")
btn_avatar = telebot.types.KeyboardButton("Сменить аватар")
btn_back_prof = telebot.types.KeyboardButton("🔙 Назад")
profile_menu.add(btn_nick, btn_desc, btn_avatar, btn_back_prof)

online_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_random = telebot.types.KeyboardButton("Случайный соперник")
btn_id = telebot.types.KeyboardButton("По ID")
btn_back_online = telebot.types.KeyboardButton("🔙 Назад")
online_menu.add(btn_random, btn_id, btn_back_online)


# Генерация реперского стиха для баттла (в стиле поэтов)
def generate_poem(author, round_num=1):
    prompt_dict = {
        "Гоголь": f"Напиши 4-строчный реп в мрачном стиле Гоголя, раунд {round_num}. Используй темные образы (ночь, тени, зло), жесткий ритм и четкую рифму (1-3, 2-4 или 1-4, 2-3).",
        "Пушкин": f"Напиши 4-строчный реп в романтическом стиле Пушкина, раунд {round_num}. Используй светлые образы (луна, любовь, звезды), плавный ритм и четкую рифму (1-3, 2-4 или 1-4, 2-3).",
        "Есенин": f"Напиши 4-строчный реп в лиричном стиле Есенина, раунд {round_num}. Используй природные образы (поля, реки, лес), душевный ритм и четкую рифму (1-3, 2-4 или 1-4, 2-3).",
        "Лермонтов": f"Напиши 4-строчный реп в драматичном стиле Лермонтова, раунд {round_num}. Используй образы одиночества и борьбы (горы, буря, судьба), мощный ритм и четкую рифму (1-3, 2-4 или 1-4, 2-3).",
        "Толстой": f"Напиши 4-строчный реп в философском стиле Толстого, раунд {round_num}. Используй образы жизни и морали (душа, правда, путь), глубокий ритм и четкую рифму (1-3, 2-4 или 1-4, 2-3)."
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system",
             "content": "Ты репер в стиле русских классиков. Пиши ровно 4 строки с яркими образами, четким ритмом и звучной рифмой (1-3, 2-4 или 1-4, 2-3). Строго следи за стилем и рифмой, без лишних слов."},
            {"role": "user", "content": prompt_dict[author]}
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
        return "\n".join(lines[:4])
    except requests.exceptions.RequestException as e:
        return f"Ошибка: {str(e)}"


# Оценка стиха
def evaluate_poem(poem, is_user=False):
    prompt = f"Оцени этот 4-строчный реп по шкале 1-10. Учитывай ритм, четкость рифмы и качество текста. Если рифмы нет или текст короче 4 строк, снижай оценку. Верни только число.\n\n{poem}"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-4o-mini",
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


# Генерация рифмы для второй игры (строгая рифма, без репа)
def generate_rhyme(user_line):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system",
             "content": "Пиши только на русском языке. Продолжай строку пользователя одной полноценной строкой, строго рифмуя последнее слово с последним словом строки пользователя. Не повторяй последнее слово строки пользователя. Рифма должна быть в конце строки. Пример: если строка 'Я иду домой', ответ 'Встречу вечер золотой', но не 'Я пришёл домой'. Без лишних слов."},
            {"role": "user", "content": f"Продолжи одной строкой, зарифмуй последнее слово строки '{user_line}'."}
        ],
        "max_tokens": 50,
        "temperature": 0.8
    }
    try:
        response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"Ошибка: {str(e)}"


@bot.message_handler(commands=['start'])
def main(message):
    user_states[message.chat.id] = None
    if message.chat.id not in profiles:
        profiles[message.chat.id]["nick"] = message.from_user.username or f"User_{message.chat.id}"
    bot.send_message(message.chat.id, (
        "🎤 Привет! Это реп-арена.\n"
        "Реп-баттл: с поэтами, до 2 побед, max 3 раунда.\n"
        "Игра в рифму: кидай строку, я зарифмую.\n"
        "Выбирай!"
    ), reply_markup=start_markup)


@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle_message(message):
    chat_id = message.chat.id
    username = message.from_user.username or str(chat_id)

    if message.text == "🎤 Реп-баттл":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "Выбери соперника:", reply_markup=rivals_markup)

    elif message.text == "🎵 Игра в рифму":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "Кидай строку, я зарифмую!", reply_markup=game_menu)
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

    elif message.text == "👤 Профиль":
        profile = profiles[chat_id]
        nick = profile["nick"]
        desc = profile["desc"]
        avatar = profile["avatar"]
        msg = f"ID: {chat_id}\nНик: {nick}\nОписание: {desc}"
        if avatar:
            bot.send_photo(chat_id, avatar, caption=msg, reply_markup=profile_menu)
        else:
            bot.send_message(chat_id, msg + "\nАватар: Не установлен", reply_markup=profile_menu)

    elif message.text == "🌐 Онлайн":
        bot.send_message(chat_id, "Выбери режим:", reply_markup=online_menu)

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

    elif message.text in ["Гоголь", "Пушкин", "Есенин", "Лермонтов", "Толстой"]:
        rival = message.text
        bot.send_message(chat_id, f"Соперник: {rival}. Раунд 1. Читай реп (4 строки)!", reply_markup=game_menu)
        user_states[chat_id] = {"state": "battle", "rival": rival, "round": 1, "user_wins": 0, "rival_wins": 0}
        battle_scores[chat_id] = []

    elif message.text == "🔄 Сменить поэта":
        bot.send_message(chat_id, "Выбери нового соперника:", reply_markup=rivals_markup)
        user_states[chat_id] = None

    elif message.text == "Сменить ник":
        bot.send_message(chat_id, "Введи новый ник:")
        user_states[chat_id] = "awaiting_nick"

    elif message.text == "Сменить описание":
        bot.send_message(chat_id, "Введи новое описание:")
        user_states[chat_id] = "awaiting_desc"

    elif message.text == "Сменить аватар":
        bot.send_message(chat_id, "Пришли фото для аватара:")
        user_states[chat_id] = "awaiting_avatar"

    elif message.text == "Случайный соперник":
        bot.send_message(chat_id, "Ищу случайного соперника... (пока в разработке)", reply_markup=start_markup)
        user_states[chat_id] = None

    elif message.text == "По ID":
        bot.send_message(chat_id, "Введи ID соперника:")
        user_states[chat_id] = "awaiting_online_id"

    elif chat_id in user_states:
        state = user_states[chat_id] if isinstance(user_states[chat_id], str) else user_states[chat_id].get("state")

        if state == "battle" and message.text:
            round_num = user_states[chat_id]["round"]
            rival = user_states[chat_id]["rival"]
            user_poem = message.text
            rival_poem = generate_poem(rival, round_num)
            bot.send_message(chat_id, f"Раунд {round_num}. {rival}:\n{rival_poem}")

            user_score = evaluate_poem(user_poem, is_user=True)
            if "Ошибка" in str(user_score):
                bot.send_message(chat_id, user_score)
                return
            rival_score = evaluate_poem(rival_poem)
            if "Ошибка" in str(rival_score):
                bot.send_message(chat_id, rival_score)
                return

            battle_scores[chat_id].append((user_poem, user_score, rival_poem, rival_score))

            winner = "Ты" if user_score > rival_score else rival if rival_score > user_score else "Ничья"
            bot.send_message(chat_id, f"Раунд {round_num}: {winner} впереди.")

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
                    winner_msg = f"{rival} победил {user_states[chat_id]['rival_wins']}:{user_states[chat_id]['user_wins']}."
                else:
                    winner_msg = "Ничья!"

                scores_msg = "\n".join(
                    f"Раунд {i + 1}: Ты - {s[1]}/10, {rival} - {s[3]}/10" for i, s in enumerate(battle_scores[chat_id]))
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
                rival_line = generate_rhyme(user_line)
                bot.send_message(chat_id, f"Твоя строка: {user_line}\nМоя: {rival_line}")
                user_states[chat_id]["rounds"] += 1

        elif state == "awaiting_nick" and message.text:
            profiles[chat_id]["nick"] = message.text
            bot.send_message(chat_id, "Ник изменён!", reply_markup=profile_menu)
            user_states[chat_id] = None

        elif state == "awaiting_desc" and message.text:
            profiles[chat_id]["desc"] = message.text
            bot.send_message(chat_id, "Описание изменено!", reply_markup=profile_menu)
            user_states[chat_id] = None

        elif state == "awaiting_avatar" and message.photo:
            profiles[chat_id]["avatar"] = message.photo[-1].file_id
            bot.send_message(chat_id, "Аватар изменён!", reply_markup=profile_menu)
            user_states[chat_id] = None

        elif state == "awaiting_online_id" and message.text:
            try:
                rival_id = int(message.text)
                if rival_id in profiles:
                    bot.send_message(chat_id, f"Соперник найден! Начинаем баттл с ID {rival_id} (пока в разработке)",
                                     reply_markup=start_markup)
                else:
                    bot.send_message(chat_id, "Пользователь не найден.", reply_markup=online_menu)
            except ValueError:
                bot.send_message(chat_id, "Неверный ID. Введи число.", reply_markup=online_menu)
            user_states[chat_id] = None

        elif state == "awaiting_feedback":
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
                bot.send_message(chat_id, f"Ошибка: {str(e)}. Попробуй ещё!")

    else:
        bot.send_message(chat_id, "Жми кнопки! /start — для начала.")


bot.polling(none_stop=True)