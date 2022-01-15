import logging
import os
import time

import requests
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from telegram import Bot

load_dotenv()
need_to_send_message = True  # чтобы не отправлять повторные сообщения
data = {}  # сюда буду сохранять полученные данные, чтобы не повторять
# отправку сообщения, когда снова получу эту же информацию

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
    """Функция отправляет в заданный чат Телеграмм указанный текст."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info(f'Сообщение отправлено: {message}')
    # доработать проверку на сбой при отправке сообщения


def get_api_answer(current_timestamp):
    """Функция получает ответ от API сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except HTTPError as http_err:
        logging.error(f'Возникла ошибка HTTP: {http_err}')
    except Exception as err:
        logging.error(f'При запросе возникла какая-то ошибка: {err}')
    else:
        logging.info('Отправлен запрос на сервер')
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Проблемы с API Яндекс.Практикума')


def check_response(response):
    """проверяет ответ на ошибки и возвращает список домашних работ."""
    homeworks = response.get('homeworks')
    if len(homeworks) == 0:
        logging.info('При парсинге ответа получен пустой словарь')
    return homeworks


def parse_status(homework):
    """Функция распарсивает полученный ответ."""
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        need_to_send_message = True
        if homework_name in data:
            if homework_status == data[homework_name]:
                need_to_send_message = False
            else:
                data[homework_name] = homework_status
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES[homework_status]
            return f'Изменился статус проверки работы "{homework_name}". {verdict}'
        else:
            message = (f'Получен неизвестный статус - {homework_status}')
            logging.error(message)
            return message
    except Exception:
        logging.error('При парсинге ответа не обнаружены нужные ключи')


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
    ):
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not(check_tokens()):
        logging.critical('Не получилось считать переменные окружения')
        exit

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            api_answer = get_api_answer(current_timestamp - 25 * 24 * 60 * 60)
            # что делать с теми статусами, которые уже были отправлены?
            homeworks = check_response(api_answer)
            print(homeworks)
            for homework in homeworks:
                verdict_message = parse_status(homework)
                if need_to_send_message:
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
