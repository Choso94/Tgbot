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
profiles = defaultdict(lambda: {"nick": None, "battle_nick": None, "desc": "Нет описания", "avatar": None})
leaderboard_battle = defaultdict(lambda: {"wins": 0, "games": 0})
leaderboard_rhyme = defaultdict(lambda: {"longest_rounds": 0})
online_battles = {}
searching_users = set()  # Множество пользователей, находящихся в поиске

# Клавиатуры
start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
start_markup.add("🎤 Реп-баттл", "🎵 Игра в рифму")
start_markup.add("🏆 Лидерборд", "👤 Профиль")
start_markup.add("🌐 Онлайн", "Сайт", "Связь")

rivals_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
rivals_markup.add("Гоголь", "Пушкин", "Есенин", "Лермонтов", "Толстой")

game_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
game_menu.add("🔙 Назад", "🔄 Сменить поэта")

online_battle_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
online_battle_menu.add("🔙 Назад")

profile_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
profile_menu.add("Сменить ник", "Сменить описание", "Сменить аватар", "🔙 Назад")

online_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
online_menu.add("Случайный соперник", "По ID", "🔙 Назад")

battle_invite = telebot.types.InlineKeyboardMarkup()
battle_invite.add(
    telebot.types.InlineKeyboardButton("✅ Согласиться", callback_data="battle_yes"),
    telebot.types.InlineKeyboardButton("❌ Нет", callback_data="battle_no")
)

online_game = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
online_game.add("🎤 Баттл", "🔙 Назад")


# Генерация реперского стиха
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
        return f"⚠️ Ошибка генерации: {str(e)}"


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
        return f"⚠️ Ошибка оценки: {str(e)}"


# Генерация рифмы
def generate_rhyme(user_line):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system",
             "content": "Пиши только на русском языке. Продолжай строку пользователя одной полноценной строкой, строго рифмуя последнее слово с последним словом строки пользователя. Не повторяй последнее слово строки пользователя. Рифма должна быть в конце строки."},
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
        return f"⚠️ Ошибка рифмы: {str(e)}"


@bot.message_handler(commands=['start'])
def main(message):
    user_states[message.chat.id] = None
    if message.chat.id not in profiles:
        profiles[message.chat.id]["nick"] = message.from_user.username or f"User_{message.chat.id}"
    bot.send_message(message.chat.id, (
        "🎤 **Добро пожаловать в Реп-Арену!** 🎤\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎤 **Реп-баттл**: Докажи, что ты лучший!\n"
        "🎵 **Игра в рифму**: Покажи свой слог.\n"
        "🏆 **Лидерборд**: Кто в топе?\n"
        "👤 **Профиль**: Настрой свой стиль.\n"
        "🌐 **Онлайн**: Баттл с живыми игроками.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выбирай режим и врывайся!"
    ), reply_markup=start_markup)


@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note'])
def handle_message(message):
    chat_id = message.chat.id
    username = profiles[chat_id]["battle_nick"] or profiles[chat_id]["nick"]

    if message.text == "🎤 Реп-баттл":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, (
            "🎤 **Реп-баттл** 🎤\n"
            "━━━━━━━━━━━━━\n"
            "📜 Правила:\n"
            "  • 3 раунда\n"
            "  • Пиши 4 строки с рифмой\n"
            "  • До 2 побед\n"
            "━━━━━━━━━━━━━\n"
            "Выбери соперника:"
        ), reply_markup=rivals_markup)

    elif message.text == "🎵 Игра в рифму":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, (
            "🎵 **Игра в рифму** 🎵\n"
            "━━━━━━━━━━━━━\n"
            "📜 Правила:\n"
            "  • Кидай строку\n"
            "  • Я рифмую в ответ\n"
            "  • Пиши 'стоп' для финиша\n"
            "━━━━━━━━━━━━━\n"
            "Начинай!"
        ), reply_markup=game_menu)
        user_states[chat_id] = {"state": "rhyme_game", "rounds": 0}

    elif message.text == "🏆 Лидерборд":
        top_battle = sorted(leaderboard_battle.items(),
                            key=lambda x: x[1]["wins"] / x[1]["games"] if x[1]["games"] else 0, reverse=True)[:10]
        top_rhyme = sorted(leaderboard_rhyme.items(), key=lambda x: x[1]["longest_rounds"], reverse=True)[:10]
        bot.send_message(chat_id, (
                "🏆 **Лидерборд** 🏆\n"
                "━━━━━━━━━━━━━\n"
                "🎤 **Топ-10 Реп-баттл**:\n" + "\n".join(
            f"  • @{u}: {d['wins']}/{d['games']} ({d['wins'] / d['games'] * 100:.1f}%)"
            for u, d in top_battle
        ) + "\n\n🎵 **Топ-10 Игра в рифму**:\n" + "\n".join(
            f"  • @{u}: {d['longest_rounds']} раундов"
            for u, d in top_rhyme
        ) + "\n━━━━━━━━━━━━━"
        ))

    elif message.text == "👤 Профиль":
        profile = profiles[chat_id]
        nick = profile["nick"]
        battle_nick = profile["battle_nick"] or "Не задан"
        desc = profile["desc"]
        avatar = profile["avatar"]
        msg = (
            "👤 **Профиль** 👤\n"
            "━━━━━━━━━━━━━\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🎩 Ник Telegram: @{nick}\n"
            f"🎤 Ник в баттлах: {battle_nick}\n"
            f"📝 Описание: {desc}"
        )
        if avatar:
            bot.send_photo(chat_id, avatar, caption=msg, reply_markup=profile_menu, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, msg + "\n🖼 Аватар: Не установлен\n━━━━━━━━━━━━━", reply_markup=profile_menu,
                             parse_mode="Markdown")

    elif message.text == "🌐 Онлайн":
        bot.send_message(chat_id, (
            "🌐 **Онлайн-режим** 🌐\n"
            "━━━━━━━━━━━━━\n"
            "📜 Правила:\n"
            "  • Общайся или вызывай на баттл\n"
            "  • Выбери режим:\n"
            "━━━━━━━━━━━━━"
        ), reply_markup=online_menu)

    elif message.text == "Сайт":
        bot.send_message(chat_id,
                         "🌐 **Сайт**: [Перейти](https://itvdn.blob.core.windows.net/cbs-images/cbs-images-a7e0d809-f232-4073-a035-0c7083421dde.PNG)",
                         parse_mode="Markdown")

    elif message.text == "Связь":
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, (
            "📩 **Связь с создателем** 📩\n"
            "━━━━━━━━━━━━━\n"
            "Кидай текст, фото, видео, голос или кружки!\n"
            "Я получу всё 👇"
        ), reply_markup=start_markup)
        user_states[chat_id] = "awaiting_feedback"

    elif message.text == "🔙 Назад":
        if chat_id in searching_users:
            searching_users.remove(chat_id)
        user_states[chat_id] = None
        bot.send_message(chat_id, "🎉 **Выбирай режим!**", reply_markup=start_markup)

    elif message.text in ["Гоголь", "Пушкин", "Есенин", "Лермонтов", "Толстой"]:
        rival = message.text
        bot.send_message(chat_id, (
            f"🎤 **Баттл с {rival}** 🎤\n"
            "━━━━━━━━━━━━━\n"
            f"Раунд 1\n"
            "Пиши свой реп (4 строки):"
        ), reply_markup=game_menu)
        user_states[chat_id] = {"state": "battle", "rival": rival, "round": 1, "user_wins": 0, "rival_wins": 0}
        battle_scores[chat_id] = []

    elif message.text == "🔄 Сменить поэта":
        bot.send_message(chat_id, "🎤 **Выбери нового соперника**:", reply_markup=rivals_markup)
        user_states[chat_id] = None

    elif message.text == "Сменить ник":
        bot.send_message(chat_id, (
            "✏️ **Смена ника для баттлов** ✏️\n"
            "━━━━━━━━━━━━━\n"
            "Введи новый ник (Telegram-ник не изменится):"
        ))
        user_states[chat_id] = "awaiting_nick"

    elif message.text == "Сменить описание":
        bot.send_message(chat_id, (
            "📝 **Смена описания** 📝\n"
            "━━━━━━━━━━━━━\n"
            "Введи новое описание:"
        ))
        user_states[chat_id] = "awaiting_desc"

    elif message.text == "Сменить аватар":
        bot.send_message(chat_id, (
            "🖼 **Смена аватара** 🖼\n"
            "━━━━━━━━━━━━━\n"
            "Пришли фото для аватара:"
        ))
        user_states[chat_id] = "awaiting_avatar"

    elif message.text == "Случайный соперник":
        if chat_id in searching_users:
            bot.send_message(chat_id, (
                "🔍 **Ты уже в поиске!** 🔍\n"
                "━━━━━━━━━━━━━\n"
                "Жди соперника..."
            ))
        else:
            searching_users.add(chat_id)
            available_users = [uid for uid in searching_users if uid != chat_id]
            if not available_users:
                bot.send_message(chat_id, (
                    "🔍 **Поиск соперника** 🔍\n"
                    "━━━━━━━━━━━━━\n"
                    "Жди, пока кто-то тоже выберет 'Случайный соперник'..."
                ), reply_markup=online_menu)
                user_states[chat_id] = {"state": "searching"}
            else:
                rival_id = random.choice(available_users)
                searching_users.remove(chat_id)
                searching_users.remove(rival_id)
                bot.send_message(chat_id, (
                    f"💬 **Соперник найден!** 💬\n"
                    "━━━━━━━━━━━━━\n"
                    f"Ты на связи с @{profiles[rival_id]['nick']}\n"
                    "Пиши или вызывай на баттл!"
                ), reply_markup=online_game)
                bot.send_message(rival_id, (
                    f"💬 **Соперник найден!** 💬\n"
                    "━━━━━━━━━━━━━\n"
                    f"Ты на связи с @{username}\n"
                    "Пиши или вызывай на баттл!"
                ), reply_markup=online_game)
                user_states[chat_id] = {"state": "online_chat", "rival_id": rival_id}
                user_states[rival_id] = {"state": "online_chat", "rival_id": chat_id}

    elif message.text == "По ID":
        bot.send_message(chat_id, (
            "🆔 **Выбор по ID** 🆔\n"
            "━━━━━━━━━━━━━\n"
            "Введи ID соперника:"
        ))
        user_states[chat_id] = "awaiting_online_id"

    elif message.text == "🎤 Баттл" and chat_id in user_states and user_states[chat_id].get("state") == "online_chat":
        rival_id = user_states[chat_id]["rival_id"]
        bot.send_message(rival_id, (
            f"🎤 **Вызов на баттл!** 🎤\n"
            "━━━━━━━━━━━━━\n"
            f"@{username} вызывает тебя!"
        ), reply_markup=battle_invite)
        bot.send_message(chat_id, (
            f"📩 **Приглашение отправлено** 📩\n"
            "━━━━━━━━━━━━━\n"
            f"Ждём ответа от @{profiles[rival_id]['nick']}..."
        ))
        online_battles[rival_id] = chat_id

    elif chat_id in user_states:
        state = user_states[chat_id] if isinstance(user_states[chat_id], str) else user_states[chat_id].get("state") if \
        user_states[chat_id] else None

        if state == "battle" and message.text:
            round_num = user_states[chat_id]["round"]
            rival = user_states[chat_id]["rival"]
            user_poem = message.text
            rival_poem = generate_poem(rival, round_num)
            bot.send_message(chat_id, (
                f"🎤 **Раунд {round_num}** 🎤\n"
                "━━━━━━━━━━━━━\n"
                f"**Ты**:\n{user_poem}\n\n"
                f"**{rival}**:\n{rival_poem}"
            ))

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
            bot.send_message(chat_id, (
                f"🏅 **Результат раунда {round_num}** 🏅\n"
                "━━━━━━━━━━━━━\n"
                f"Ты: {user_score}/10\n"
                f"{rival}: {rival_score}/10\n"
                f"👑 Победитель: {winner}"
            ))

            if user_score > rival_score:
                user_states[chat_id]["user_wins"] += 1
            elif rival_score > user_score:
                user_states[chat_id]["rival_wins"] += 1

            if user_states[chat_id]["user_wins"] == 2 or user_states[chat_id]["rival_wins"] == 2 or round_num == 3:
                leaderboard_battle[username]["games"] += 1
                if user_states[chat_id]["user_wins"] > user_states[chat_id]["rival_wins"]:
                    leaderboard_battle[username]["wins"] += 1
                    winner_msg = f"🏆 Ты победил со счётом {user_states[chat_id]['user_wins']}:{user_states[chat_id]['rival_wins']}!"
                elif user_states[chat_id]["rival_wins"] > user_states[chat_id]["user_wins"]:
                    winner_msg = f"🏆 {rival} победил со счётом {user_states[chat_id]['rival_wins']}:{user_states[chat_id]['user_wins']}!"
                else:
                    winner_msg = "🤝 Ничья!"

                scores_msg = "\n".join(
                    f"Раунд {i + 1}: Ты - {s[1]}/10 | {rival} - {s[3]}/10"
                    for i, s in enumerate(battle_scores[chat_id])
                )
                bot.send_message(chat_id, (
                    f"🎉 **Итоги баттла** 🎉\n"
                    "━━━━━━━━━━━━━\n"
                    f"{scores_msg}\n"
                    f"━━━━━━━━━━━━━\n"
                    f"{winner_msg}"
                ), reply_markup=start_markup)
                user_states[chat_id] = None
                del battle_scores[chat_id]
            else:
                user_states[chat_id]["round"] += 1
                bot.send_message(chat_id, (
                    f"🎤 **Раунд {round_num + 1}** 🎤\n"
                    "━━━━━━━━━━━━━\n"
                    "Пиши свой реп (4 строки):"
                ), reply_markup=game_menu)

        elif state == "rhyme_game" and message.text:
            if message.text.lower() == "стоп":
                rounds = user_states[chat_id]["rounds"]
                if rounds > leaderboard_rhyme[username]["longest_rounds"]:
                    leaderboard_rhyme[username]["longest_rounds"] = rounds
                bot.send_message(chat_id, (
                    f"🎵 **Игра окончена** 🎵\n"
                    "━━━━━━━━━━━━━\n"
                    f"Ты прошёл {rounds} раундов!"
                ), reply_markup=start_markup)
                user_states[chat_id] = None
            else:
                user_line = message.text
                rival_line = generate_rhyme(user_line)
                if "Ошибка" in rival_line:
                    bot.send_message(chat_id, rival_line)
                else:
                    bot.send_message(chat_id, (
                        f"🎵 **Рифма** 🎵\n"
                        "━━━━━━━━━━━━━\n"
                        f"Ты: {user_line}\n"
                        f"Я: {rival_line}"
                    ))
                    user_states[chat_id]["rounds"] += 1

        elif state == "awaiting_nick" and message.text:
            profiles[chat_id]["battle_nick"] = message.text
            bot.send_message(chat_id, (
                "✅ **Ник для баттлов изменён!** ✅\n"
                "━━━━━━━━━━━━━\n"
                f"Теперь ты @{message.text} в баттлах."
            ), reply_markup=profile_menu)
            user_states[chat_id] = None

        elif state == "awaiting_desc" and message.text:
            profiles[chat_id]["desc"] = message.text
            bot.send_message(chat_id, (
                "✅ **Описание обновлено!** ✅\n"
                "━━━━━━━━━━━━━\n"
                f"Новое описание: {message.text}"
            ), reply_markup=profile_menu)
            user_states[chat_id] = None

        elif state == "awaiting_avatar" and message.photo:
            profiles[chat_id]["avatar"] = message.photo[-1].file_id
            bot.send_message(chat_id, (
                "✅ **Аватар обновлён!** ✅\n"
                "━━━━━━━━━━━━━\n"
                "Проверь в профиле!"
            ), reply_markup=profile_menu)
            user_states[chat_id] = None

        elif state == "awaiting_online_id" and message.text:
            try:
                rival_id = int(message.text)
                if rival_id in profiles and rival_id != chat_id:
                    bot.send_message(chat_id, (
                        f"💬 **Соперник найден!** 💬\n"
                        "━━━━━━━━━━━━━\n"
                        f"Ты на связи с @{profiles[rival_id]['nick']}\n"
                        "Пиши или вызывай на баттл!"
                    ), reply_markup=online_game)
                    bot.send_message(rival_id, (
                        f"💬 **Тебя выбрали!** 💬\n"
                        "━━━━━━━━━━━━━\n"
                        f"@{username} хочет общаться или баттлить!"
                    ), reply_markup=online_game)
                    user_states[chat_id] = {"state": "online_chat", "rival_id": rival_id}
                    user_states[rival_id] = {"state": "online_chat", "rival_id": chat_id}
                else:
                    bot.send_message(chat_id, (
                        "❌ **Ошибка** ❌\n"
                        "━━━━━━━━━━━━━\n"
                        "Пользователь не найден или это ты!"
                    ), reply_markup=online_menu)
            except ValueError:
                bot.send_message(chat_id, (
                    "❌ **Ошибка** ❌\n"
                    "━━━━━━━━━━━━━\n"
                    "Введи корректный ID (число)!"
                ), reply_markup=online_menu)

        elif state == "online_chat" and message.text:
            rival_id = user_states[chat_id]["rival_id"]
            try:
                bot.send_message(rival_id, (
                    f"💬 **Сообщение от @{username}** 💬\n"
                    "━━━━━━━━━━━━━\n"
                    f"{message.text}"
                ), reply_markup=online_game)
                bot.send_message(chat_id, (
                    f"📤 **Отправлено @{profiles[rival_id]['nick']}** 📤\n"
                    "━━━━━━━━━━━━━\n"
                    f"{message.text}"
                ))
            except Exception as e:
                bot.send_message(chat_id, (
                    f"❌ **Ошибка отправки** ❌\n"
                    "━━━━━━━━━━━━━\n"
                    f"{str(e)}"
                ))

        elif state == "online_battle" and message.text:
            round_num = user_states[chat_id]["round"]
            rival_id = user_states[chat_id]["rival_id"]
            user_poem = message.text

            if "is_initiator" in user_states[chat_id] and user_states[chat_id]["is_initiator"]:
                battle_scores[chat_id].append((user_poem, None))
                bot.send_message(rival_id, (
                    f"🎤 **Раунд {round_num}** 🎤\n"
                    "━━━━━━━━━━━━━\n"
                    f"@{username}:\n{user_poem}\n\n"
                    "Твой ход! Пиши реп (4 строки):"
                ), reply_markup=online_battle_menu)
                bot.send_message(chat_id, (
                    f"🎤 **Раунд {round_num}** 🎤\n"
                    "━━━━━━━━━━━━━\n"
                    f"Твой реп:\n{user_poem}\n\n"
                    f"Ждём ответа от @{profiles[rival_id]['nick']}..."
                ))
                return

            # Ответ второго игрока
            rival_poem = battle_scores[chat_id][round_num - 1][0]
            user_score = evaluate_poem(user_poem, is_user=True)
            rival_score = evaluate_poem(rival_poem)
            battle_scores[chat_id][round_num - 1] = (rival_poem, rival_score, user_poem, user_score)
            battle_scores[rival_id] = battle_scores[chat_id]  # Синхронизация

            bot.send_message(chat_id, (
                f"🎤 **Раунд {round_num}** 🎤\n"
                "━━━━━━━━━━━━━\n"
                f"Ты:\n{user_poem}\n\n"
                f"@{profiles[rival_id]['nick']}:\n{rival_poem}"
            ))
            bot.send_message(rival_id, (
                f"🎤 **Раунд {round_num}** 🎤\n"
                "━━━━━━━━━━━━━\n"
                f"@{username}:\n{rival_poem}\n\n"
                f"Ты:\n{user_poem}"
            ))

            bot.send_message(chat_id, (
                f"🏅 **Результат раунда {round_num}** 🏅\n"
                "━━━━━━━━━━━━━\n"
                f"Ты: {user_score}/10\n"
                f"@{profiles[rival_id]['nick']}: {rival_score}/10"
            ))
            bot.send_message(rival_id, (
                f"🏅 **Результат раунда {round_num}** 🏅\n"
                "━━━━━━━━━━━━━\n"
                f"@{username}: {rival_score}/10\n"
                f"Ты: {user_score}/10"
            ))

            if user_score > rival_score:
                user_states[chat_id]["user_wins"] += 1
                user_states[rival_id]["rival_wins"] += 1
            elif rival_score > user_score:
                user_states[chat_id]["rival_wins"] += 1
                user_states[rival_id]["user_wins"] += 1

            if round_num == 3:
                leaderboard_battle[username]["games"] += 1
                leaderboard_battle[profiles[rival_id]["nick"]]["games"] += 1
                if user_states[chat_id]["user_wins"] > user_states[chat_id]["rival_wins"]:
                    leaderboard_battle[username]["wins"] += 1
                    winner_msg = f"🏆 Ты победил {user_states[chat_id]['user_wins']}:{user_states[chat_id]['rival_wins']}!"
                    rival_msg = f"🏆 @{username} победил {user_states[chat_id]['rival_wins']}:{user_states[chat_id]['user_wins']}!"
                elif user_states[chat_id]["rival_wins"] > user_states[chat_id]["user_wins"]:
                    leaderboard_battle[profiles[rival_id]["nick"]]["wins"] += 1
                    winner_msg = f"🏆 @{profiles[rival_id]['nick']} победил {user_states[chat_id]['rival_wins']}:{user_states[chat_id]['user_wins']}!"
                    rival_msg = f"🏆 Ты победил {user_states[chat_id]['user_wins']}:{user_states[chat_id]['rival_wins']}!"
                else:
                    winner_msg = "🤝 Ничья!"
                    rival_msg = "🤝 Ничья!"

                scores_msg_user = "\n".join(
                    f"Раунд {i + 1}: Ты - {s[1]}/10 | @{profiles[rival_id]['nick']} - {s[3]}/10"
                    for i, s in enumerate(battle_scores[chat_id])
                )
                scores_msg_rival = "\n".join(
                    f"Раунд {i + 1}: @{username} - {s[1]}/10 | Ты - {s[3]}/10"
                    for i, s in enumerate(battle_scores[chat_id])
                )
                bot.send_message(chat_id, (
                    f"🎉 **Итоги баттла** 🎉\n"
                    "━━━━━━━━━━━━━\n"
                    f"{scores_msg_user}\n"
                    f"━━━━━━━━━━━━━\n"
                    f"{winner_msg}"
                ), reply_markup=start_markup)
                bot.send_message(rival_id, (
                    f"🎉 **Итоги баттла** 🎉\n"
                    "━━━━━━━━━━━━━\n"
                    f"{scores_msg_rival}\n"
                    f"━━━━━━━━━━━━━\n"
                    f"{rival_msg}"
                ), reply_markup=start_markup)
                user_states[chat_id] = None
                user_states[rival_id] = None
                del battle_scores[chat_id]
                del battle_scores[rival_id]
            else:
                user_states[chat_id]["round"] += 1
                user_states[rival_id]["round"] += 1
                bot.send_message(chat_id, (
                    f"🎤 **Раунд {round_num + 1}** 🎤\n"
                    "━━━━━━━━━━━━━\n"
                    "Пиши свой реп (4 строки):"
                ), reply_markup=online_battle_menu)
                bot.send_message(rival_id, (
                    f"🎤 **Раунд {round_num + 1}** 🎤\n"
                    "━━━━━━━━━━━━━\n"
                    f"Ждём репа от @{username}..."
                ))

        elif state == "awaiting_feedback":
            try:
                if message.text:
                    bot.send_message(MY_CHAT_ID, f"📩 **Связь от @{username}**:\n{message.text}")
                elif message.photo:
                    bot.forward_message(MY_CHAT_ID, chat_id, message.message_id)
                elif message.video:
                    bot.forward_message(MY_CHAT_ID, chat_id, message.message_id)
                elif message.voice:
                    bot.forward_message(MY_CHAT_ID, chat_id, message.message_id)
                elif message.video_note:
                    bot.forward_message(MY_CHAT_ID, chat_id, message.message_id)
                bot.send_message(chat_id, (
                    "✅ **Фидбек отправлен!** ✅\n"
                    "━━━━━━━━━━━━━\n"
                    "Спасибо, я всё получил!"
                ), reply_markup=start_markup)
                user_states[chat_id] = None
            except Exception as e:
                bot.send_message(chat_id, f"❌ Ошибка: {str(e)}. Попробуй ещё!")

    else:
        bot.send_message(chat_id, (
            "🎉 **Жми кнопки ниже!** 🎉\n"
            "━━━━━━━━━━━━━\n"
            "Или используй /start для начала."
        ))


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    if call.data == "battle_yes":
        if chat_id in online_battles:
            inviter_id = online_battles[chat_id]
            bot.send_message(inviter_id, (
                f"✅ **@{profiles[chat_id]['nick']} согласился!** ✅\n"
                "━━━━━━━━━━━━━\n"
                "Раунд 1\n"
                "Пиши свой реп (4 строки):"
            ), reply_markup=online_battle_menu)
            bot.send_message(chat_id, (
                f"🎤 **Баттл начался!** 🎤\n"
                "━━━━━━━━━━━━━\n"
                f"Ждём репа от @{profiles[inviter_id]['nick']}..."
            ), reply_markup=online_battle_menu)
            user_states[inviter_id] = {"state": "online_battle", "rival_id": chat_id, "round": 1, "user_wins": 0,
                                       "rival_wins": 0, "is_initiator": True}
            user_states[chat_id] = {"state": "online_battle", "rival_id": inviter_id, "round": 1, "user_wins": 0,
                                    "rival_wins": 0}
            battle_scores[inviter_id] = []
            battle_scores[chat_id] = []
            del online_battles[chat_id]
    elif call.data == "battle_no":
        if chat_id in online_battles:
            inviter_id = online_battles[chat_id]
            bot.send_message(inviter_id, (
                f"❌ **@{profiles[chat_id]['nick']} отказался** ❌\n"
                "━━━━━━━━━━━━━\n"
                "Ищи нового соперника!"
            ))
            del online_battles[chat_id]


bot.polling(none_stop=True)