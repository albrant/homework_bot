import logging
import os
import time

import requests
from telegram import Bot
from dotenv import load_dotenv

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
    # доработать проверку на сбой при отправке сообщения


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homeworks = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return homeworks.json()


def check_response(response):
    if response.status_code == 200:
        answer = response.json().get('homeworks')
        if len(answer) == 0:
            logging.info(f'При парсинге ответа получен пустой словарь')
        return answer
    else:
        raise Exception('Проблемы с API практикума')


def parse_status(homework):
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES[homework_status]
            return f'Изменился статус проверки работы "{homework_name}". {verdict}'
        else:
            message = (f'Получен неизвестный статус - {homework_status}')
            logging.error(message)
            return message
            
    except Exception as error:
        logging.error(f'При парсинге ответа не обнаружены нужные ключи')


def check_tokens():
    if PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
        return False
    return True


def main():
    """Основная логика работы бота."""

    if not(check_tokens()):
        logging.critical(f'Не получилось считать переменные окружения')
        exit
        

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    #send_message(bot, 'Приложение запущено')

    while True:
        try:
            api_answer = get_api_answer(current_timestamp - 25*24*60*60) 
            # что делать с теми статусами, которые уже были отправлены?
            homeworks = check_response(api_answer)
            print(homeworks)
            for homework in homeworks:
                verdict_message = parse_status(homework)
                send_message(bot, verdict_message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()
