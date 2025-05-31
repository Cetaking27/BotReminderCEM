from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import os

# 📦 Charger le token depuis .env
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

print("le Token est:", TOKEN)
if not TOKEN:
    raise ValueError("le token n'est pas pris en compte.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_ids = set()

main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="✅ Confirmer"),
            types.KeyboardButton(text="❌ abandonner")
        ]
    ],
    resize_keyboard=True
)

GROUP_ID = int(os.getenv('GROUP_ID'))
present_users = set()
absent_users = set()

@dp.message(Command(commands=['start', 'help']))
async def start_command(message: types.Message):
    await message.answer(
        text="🔔 Bienvenue sur le bot de la CEM ! Clique pour confirmer ton inscription.",
        reply_markup=main_keyboard
    )

@dp.message(Command(commands=['rapport']))
async def send_report(message: types.Message):
    await send_group_report()

@dp.message(Command(commands=['rappel']))
async def manual_reminder(message: types.Message):
    await send_reminders()
    await message.answer("📨 Rappels envoyés manuellement.")

@dp.message()
async def handle_reply(message: types.Message):
    if message.chat.type != "private":
        return

    user_ids.add(message.from_user.id)
    user = f"{message.from_user.full_name} (@{message.from_user.username or 'aucun'})"

    if message.text == "✅ Confirmer":
        present_users.add(user)
        absent_users.discard(user)
        await message.answer(
            text="Merci pour la confirmation de votre présence au culte du Dimanche.\nQue DIEU vous bénisse.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    elif message.text == "❌ abandonner":
        absent_users.add(user)
        present_users.discard(user)
        await message.answer(
            text="C'est vraiment dommage que vous ne soyez pas présent pour le prochain culte.\nJe ne connais pas la raison mais que Dieu vous fortifie.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    elif message.text.lower() == "bonjour":
        await message.answer(
            text="Bonjour ! Je suis le bot de la CEM. Clique sur un bouton ci-dessous.",
            reply_markup=main_keyboard
        )
    else:
        await message.answer(
            text="Désolé, je ne sais pas de quoi vous parlez. Merci de cliquer sur l'un des boutons ci-dessous pour confirmer ou abandonner.",
            reply_markup=main_keyboard
        )

async def send_group_report():
    present = "\n".join([f"- {user}" for user in present_users]) or "Aucun"
    absent = "\n".join([f"- {user}" for user in absent_users]) or "Aucun"
    report = (
        "📋 *Rapport de présence CEM*\n\n"
        f"✅ Présents ({len(present_users)}) :\n{present}\n\n"
        f"❌ Absents ({len(absent_users)}) :\n{absent}"
    )
    await bot.send_message(GROUP_ID, report, parse_mode="Markdown")
    await bot.send_message(GROUP_ID, "✅ Rapport de présence publié avec succès.")

async def send_reminders():
    for user_id in user_ids:
        try:
            chat = await bot.get_chat(user_id)
            if chat.type != "private":
                continue
            await bot.send_message(
                user_id,
                "⛪️ Rappel : N'oubliez pas le culte ce dimanche ! Merci de confirmer ou d'abandonner votre présence."
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi à {user_id}: {e}")
    
    # ✅ Vider les anciennes présences après envoi
    present_users.clear()
    absent_users.clear()

async def on_startup():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        CronTrigger(day_of_week='sat', hour=18, minute=0, timezone="Europe/Moscow")
    )
    scheduler.add_job(
        send_group_report,
        CronTrigger(day_of_week='sat', hour=19, minute=0, timezone="Europe/Moscow")
    )
    scheduler.start()

async def main():
    print('✅ Bot en ligne')
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup()

    # # Pour tests uniquement (enlève-les en prod si besoin)
    # await send_reminders()
    # await send_group_report()

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot arrêté")
