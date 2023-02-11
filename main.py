import requests, time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ContentType, File
import logging
from pathlib import Path
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token='')
dp = Dispatcher(bot)

secret_key = ''


async def handle_file(file: File, file_name: str, path: str, mes: types.Message):
    Path(f"{path}").mkdir(parents=True, exist_ok=True)
    await bot.download_file(file_path=file.file_path, destination=f"{path}/{file_name}")
    await speech_to_text(f"{path}/{file_name}", mes)
    os.remove(f"{path}/{file_name}")


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Присылай мне свои голосовые сообщения, а я сделаю из них текст")


@dp.message_handler(content_types=[ContentType.VOICE])
async def voice_message_handler(message: types.Message):
    voice = await message.voice.get_file()
    path = "\\voices"
    await bot.send_message(message.chat.id, "Обрабатываю!")
    await handle_file(file=voice, file_name=f"{voice.file_id}.ogg", path=path, mes=message)


async def speech_to_text(voice, message: types.Message):
    def get_results(config):
        endpoint = "https://api.speechtext.ai/results?"
        while True:
            results = requests.get(endpoint, params=config).json()
            if "status" not in results:
                break
            print(f"Task status: {results['status']}")
            if results["status"] == 'failed':
                print("The task is failed: {}".format(results))
                break
            if results["status"] == 'finished':
                break
            time.sleep(3)
        return [results["results"]["transcript"], results["remaining seconds"]]

    with open(voice, mode="rb") as file:
        post_body = file.read()
    API_URL = "https://api.speechtext.ai/recognize?"
    header = {'Content-Type': "application/octet-stream"}
    options = {
        "key": secret_key,
        "language": "ru-RU",
        "punctuation": True,
        "format": "mp3"
    }
    r = requests.post(API_URL, headers=header, params=options, data=post_body).json()
    task = r["id"]
    params = {
        "key": secret_key,
        "task": task,
        "summary": True,
        "summary_size": 15,
        "highlights": False,
        "max_keywords": 10
    }
    transcription = get_results(params)
    logger.info("voice of: %s, text: %s", message.from_user.username, transcription[0])
    if transcription[0] != '':
        await bot.send_message(message.chat.id, transcription[0])
    else:
        await bot.send_message(message.chat.id, "Ваше сообщение пустое!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
