# homework_bot
### Описание проекта:
Бот для проверки статуса домашней работы, присылает сообщение в Telegram если статут работы изменился. Использует API Практикум.Домашка. Реализован с помощью библиотеки python telegram bot. Ведётся логирование.
### Технологии:
Python, Telegram API, Yandex.Prakticum API, Git
### Запуск проекта:
- Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/DOSuzer/homework_bot.git
cd homework_bot
```
- Создать и активировать виртуальное окружение:
```
python -m venv venv 
source venv/bin/activate (Mac, Linux)
source venv/scripts/activate (Windows)
```
- Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip 
pip install -r requirements.txt
```
- Создать файл .env и заполнить своими данными:
1. Получить PRACTICUM_TOKEN для доступа к Домашке можно по ссылке https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
2. TELEGRAM_TOKEN выдаст @BotFather при создании бота
3. TELEGRAM_CHAT_ID спросить у бота @userinfobot
```
PRACTICUM_TOKEN='token'
TELEGRAM_TOKEN='token'
TELEGRAM_CHAT_ID=<your chat id>
```
- Запустить бота:
```
python homework.py
```
