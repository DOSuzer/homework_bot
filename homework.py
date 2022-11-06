import logging
import os
import requests
import sys
import time

from dotenv import load_dotenv
from telegram import Bot, TelegramError


formatter = '%(asctime)s, %(levelname)s, %(message)s'
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(formatter))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)

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
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено')
    except TelegramError as error:
        logger.error('Сообщение не отпралено: {}'.format(error))


def get_api_answer(current_timestamp):
    """Получаем ответ API-сервиса и преобразуем JSON к типам данных Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    error_text = ('Сбой в работе программы: Эндпоинт {} '
                  'недоступен. Код ответа API: {}')
    if response.status_code == 408:
        raise Exception(error_text.format(ENDPOINT, 408))
    elif response.status_code == 404:
        raise Exception(error_text.format(ENDPOINT, 404))
    elif response.status_code == 500:
        raise Exception(error_text.format(ENDPOINT, 500))
    else:
        response = response.json()
        return response


def check_response(response):
    """Проверка соответствия ответа сервера ожиданиям."""
    if isinstance(response, dict):
        homeworks = response.get('homeworks')
    elif isinstance(response, list):
        homeworks = response[0].get('homeworks')
    else:
        raise Exception('Ответ API некорректен, неверный тип данных!')
    if homeworks is not None:
        if isinstance(homeworks, list):
            return homeworks
        else:
            raise Exception('Ответ API некорректен, по ключю "homeworks" '
                            'получен не список!')
    else:
        raise Exception('Ответ API некорректен, '
                        'отсутствует ключ "homeworks"!')


def parse_status(homework):
    """Получаем статус домашней работы."""
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('Не удалось получить статус работы!')
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Не удалось получить название работы!')
    if homework_status not in HOMEWORK_STATUSES.keys():
        raise Exception(
            ('Неизвестный статус проверки homework: {}!'
             ).format(homework_status)
        )
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия переменных окружения."""
    token_dict = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
                  'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
                  'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID}
    result = True
    for key, value in token_dict.items():
        if value is None:
            result = False
            logger.critical('Отсутствует токен "{}"'.format(key))
    return result


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise Exception('Отсутствуют переменные окружения!')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_status = 'Статус не обновлялся'
    no_changes = 'Статус не обновлялся'
    sent_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework_list = check_response(response)
            if len(homework_list) == 0:
                status = 'Статус не обновлялся'
                logger.debug('Отсутствие в ответе новых статусов')
            else:
                status = parse_status(homework_list[0])
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != sent_message:
                send_message(bot, message)
                sent_message = message
        else:
            if status != no_changes and old_status != status:
                send_message(bot, status)
                old_status = status
                current_timestamp = int(time.time())
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
