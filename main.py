import time
import threading
import requests
import pandas as pd
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from config import TELEGRAM_BOT_TOKEN, cookies, headers  # Импортируем конфигурацию


# Функция для отправки запроса и фильтрации данных
def get_filtered_data():
    params = {
        "userId": 69511891,
        "tokenId": "USDT",
        "currencyId": "RUB",
        "payment": ["377"],
        "side": "1",
        "size": "10",
        "page": "1"
    }

    # Отправляем запрос с куками и заголовками
    response = requests.post(
        url="https://api2.bybit.com/fiat/otc/item/online",
        json=params,
        cookies=cookies,  # Используем куки из config.py
        headers=headers  # Используем заголовки из config.py
    ).json()

    data = {
        'nickName': [],
        'price': [],
        'maxAmount': [],
        'remark': []
    }

    for item in response['result']['items']:
        data['nickName'].append(item['nickName'])
        data['price'].append(item['price'])
        data['maxAmount'].append(item['maxAmount'])
        data['remark'].append(item['remark'])

    df = pd.DataFrame(data)

    # Преобразование столбцов в числовой формат
    df['maxAmount'] = pd.to_numeric(df['maxAmount'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # Фильтрация данных
    filtered_df = df[(df['maxAmount'] > 1) & (df['price'] < 97)]

    return filtered_df


# Функция для преобразования данных в удобный формат для отправки
def format_filtered_data(filtered_df):
    # Если данных нет, возвращаем None
    if filtered_df.empty:
        return None

    # Преобразование строки данных в красивый текст
    formatted_data = []
    for index, row in filtered_df.iterrows():
        formatted_data.append(
            f"Продавец: {row['nickName']}\nЦена: {row['price']}\nМакс. сумма: {row['maxAmount']}\nКомментарий: {row['remark']}\n"
        )

    return "\n".join(formatted_data)


# Функция для отправки обновлений данных в чат
def send_data(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    def fetch_and_send():
        previous_data = None  # Храним предыдущие данные для сравнения

        while True:
            # Получаем отфильтрованные данные
            filtered_data = get_filtered_data()

            # Преобразуем данные в строку для отправки
            formatted_message = format_filtered_data(filtered_data)

            # Отправляем сообщение только если есть новые данные и они отличаются от предыдущих
            if formatted_message and formatted_message != previous_data:
                context.bot.send_message(chat_id=chat_id, text=formatted_message)
                previous_data = formatted_message

            # Ожидаем 5 секунд перед следующим запросом
            time.sleep(5)

    # Запускаем фоновый поток для периодических запросов
    threading.Thread(target=fetch_and_send, daemon=True).start()


# Основная функция для запуска бота
def main():
    # Инициализация бота
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчик команды /start
    dispatcher.add_handler(CommandHandler("start", send_data))

    # Запуск бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
