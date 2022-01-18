import logging
import os
import time

from http import HTTPStatus
import requests
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from telegram import Bot, TelegramError
import simplejson

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
logger = logging.getLogger(__name__)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправляет в заданный чат Телеграмм указанный текст."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение отправлено: {message}')
    except TelegramError as err:
        logger.error(f'Сообщение не отправлено: {err}')


def get_api_answer(current_timestamp):
    """Функция получает ответ от API сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except TimeoutError as time_out:
        logger.error(f'Превышено время ожидания запроса: {time_out}')
    except HTTPError as http_err:
        logger.error(f'Возникла ошибка HTTP: {http_err}')
    except ConnectionError as conn_err:
        logger.error(f'Ошибка соединения с сервером: {conn_err}')
    except Exception as err:
        logger.error(f'При запросе возникла непредвиденная ошибка: {err}')
    else:
        logger.info('Отправлен запрос на сервер')
        if response.status_code == HTTPStatus.OK:
            try:
                return response.json()
            except simplejson.JSONDecodeError:
                logger.error('Не удалось преобразовать ответ к формату json')
        else:
            raise Exception('Проблемы с API Яндекс.Практикума')


def check_response(response):
    """проверяет ответ на ошибки и возвращает список домашних работ."""
    if not isinstance(response, dict):
        raise TypeError('Данные переданы не в виде словаря')
    if 'homeworks' in response:
        homeworks = response['homeworks']
    else:
        raise KeyError('Данные не имеют ключа homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Домашка пришла не в виде списка')
    if len(homeworks) == 0:
        logger.info('При парсинге ответа получен пустой список')
    return homeworks


def parse_status(homework):
    """Функция распарсивает полученный ответ."""
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        raise KeyError('При парсинге ответа не обнаружено название работы')
    if 'status' in homework:
        homework_status = homework['status']
    else:
        raise KeyError('При парсинге ответа не обнаружен статус работы')

    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        message = (f'Получен неизвестный статус - {homework_status}')
        raise Exception(message)


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
    old_message = ''  # использую эту переменную, чтобы сохранять сообщения
    if not check_tokens():
        logger.critical('Не получилось считать переменные окружения')
        exit()

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            api_answer = get_api_answer(current_timestamp)
            homeworks = check_response(api_answer)
            for hw in homeworks:
                verdict_message = parse_status(hw)
                if old_message != verdict_message:
                    old_message = verdict_message
                    send_message(bot, verdict_message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
