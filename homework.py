import logging
import os
import time

import requests
from telegram import Bot
from dotenv import load_dotenv
from telegram.ext import CommandHandler, Updater

load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_PRAKTIKUM')
TELEGRAM_TOKEN = os.getenv('TOKEN_TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info(f'Сообщение отправлено: {message}')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    ...


def check_response(response):
    return response.json()['homeworks']


def parse_status(homework):
    homework_name = ...
    homework_status = ...

    ...

    verdict = ...

    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    return True


def main():
    """Основная логика работы бота."""

    if not(check_tokens()):
        logging.error(f'Не получилось считать переменные окружения')
        exit
        

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    ...

    while True:
        try:
            response = requests.get(ENDPOINT)

            homeworks = check_response(response)
            
            if len(homeworks) > 0:
                status_key = parse_status(homeworks[-1])
                send_message(bot, HOMEWORK_STATUSES[status_key])
                

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
