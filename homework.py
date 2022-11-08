import logging
import os
import requests
import sys
import time

from dotenv import load_dotenv
from http import HTTPStatus
from telegram import Bot, TelegramError


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PR_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TG_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение в telegram пользователю."""
    try:
        logger.info(f'Отправляем сообщение в телеграм: {message}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение успешно отправлено: {message}')
    except TelegramError as error:
        logger.error('Сообщение не отпралено: {}'.format(error))


def get_api_answer(current_timestamp):
    """Получаем ответ API-сервиса и преобразуем JSON к типам данных Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    error_text = ('Сбой в работе программы: Эндпоинт {} '
                  'недоступен. Код ответа API: {}.')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise Exception
    except requests.exceptions.ConnectionError as error:
        raise Exception(
            error_text.format(
                ENDPOINT,
                error
            ) + f'параметры запроса: {ENDPOINT}, {HEADERS}, {params}'
        )
    except Exception:
        raise Exception(error_text.format(ENDPOINT, response.status_code))
    else:
        response = response.json()
        return response


def check_response(response):
    """Проверка соответствия ответа сервера ожиданиям."""
#    pytest против логгера в этой функции,
#    но он будет добавлен в финальном релизе
#    logger.info('Начата проверка ответа сервера')
    if not isinstance(response, dict):
        raise TypeError('Ответ API некорректен, неверный тип данных!')
#    logger.info('Получен словарь с данными')
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise Exception('Ответ API некорректен, '
                        'отсутствует ключ "homeworks"!')
    if not isinstance(homeworks, list):
        raise KeyError('Ответ API некорректен, по ключю "homeworks" '
                       'получен не список!')
#    logger.info('Получен список работ')
    return homeworks


def parse_status(homework):
    """Получаем статус домашней работы."""
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('Не удалось получить статус работы!')
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Не удалось получить название работы!')
    if homework_status not in HOMEWORK_STATUSES.keys():
        raise ValueError(
            ('Неизвестный статус проверки homework: {}!'
             ).format(homework_status)
        )
    return (
        f'Изменился статус проверки работы "{homework_name}".'
        f' {HOMEWORK_STATUSES.get(homework_status)}'
    )


def check_tokens():
    """Проверка наличия переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют переменные окружения!')
        sys.exit('Отсутствуют переменные окружения!')
    bot = Bot(token=TELEGRAM_TOKEN)
    old_status = 'Статус не обновлялся'
    no_changes = 'Статус не обновлялся'
    sent_message = ''
    while True:
        try:
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            homework_list = check_response(response)
            if not homework_list:
                status = 'Статус не обновлялся'
                logger.debug('Отсутствие в ответе новых статусов')
            else:
                status = parse_status(homework_list[0])
                if status != no_changes and old_status != status:
                    send_message(bot, status)
                    old_status = status
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != sent_message:
                send_message(bot, message)
                sent_message = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    formatter = '%(asctime)s, %(levelname)s, %(message)s'
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(formatter))
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    main()
