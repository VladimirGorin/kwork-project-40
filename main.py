from telethon.sync import TelegramClient
from configparser import ConfigParser
import pandas as pd
import os
import time
import re
from telethon.tl.functions.channels import JoinChannelRequest

config = ConfigParser()
config.read('config.ini')

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

client = TelegramClient(config['Telegram']['phone_number'], api_id, api_hash)

client.connect()

df = pd.read_csv('./data/ifets.csv')

result_file_path = './result.csv'
if os.path.exists(result_file_path):
    os.remove(result_file_path)

if not client.is_user_authorized():
    client.send_code_request(config['Telegram']['phone_number'])

    try:
        client.sign_in(config['Telegram']['phone_number'], input('Введите код из SMS:'))
    except Exception as e:
        if "Two-steps verification is enabled and a password is required (caused by SignInRequest)" in str(e):
            while True:
                password = input('Введите пароль: ')
                try:
                    client.sign_in(password=password)
                    break
                except Exception as e:
                    print(f"Неверный пароль. Попробуйте еще раз. Ошибка: {e}")
        else:
            print(f"Произошла ошибка: {e}")

def extract_company_info(text):
    inn_pattern = re.compile(r'ИНН: (\d+)')
    income_pattern = re.compile(r'Доходы за 2022: (.+)')
    employees_pattern = re.compile(r'Количество сотрудников: (.+)')
    email_pattern = re.compile(r'Электроная почта: (.+)')

    inn_match = re.search(inn_pattern, text)
    income_match = re.search(income_pattern, text)
    employees_match = re.search(employees_pattern, text)
    email_match = re.search(email_pattern, text)

    company_info = {
        'ИНН': inn_match.group(1).strip() if inn_match else None,
        'Доходы за 2022': income_match.group(1).strip() if income_match else None,
        'Количество сотрудников': employees_match.group(1).strip() if employees_match else None,
        'Электронная почта': email_match.group(1).strip() if email_match else None,
    }

    return company_info

def extract_company_black_list(text):
    risk_level = re.compile(r'Уровень риска: (\d+)')

    risk_level_match = re.search(risk_level, text)

    return risk_level_match.group(1).strip() if risk_level_match else None

def subscribe_to_channel(client, channel_username):
    client(JoinChannelRequest(channel_username))
    print(f'Успешно подписались на {channel_username}')

result_df_list = []



for index, row in df.iterrows():
    inn = str(row['ИНН'])

    try:
        client.send_message("https://t.me/LeakednfBot", f"/inn {inn}")

        print(f"\nПолучаем информацию по ИНН: {inn}")
        time.sleep(7)

        text = client.get_messages("https://t.me/LeakednfBot", limit=1)[0].message

        if "Поиск по России доступен" in text:
            text = client.get_messages("https://t.me/LeakednfBot", limit=2)[1].message

        company_info_match = extract_company_info(text)


        while True:
            client.send_message("https://t.me/Sveto4rus_bot", inn)
            time.sleep(5)
            text = client.get_messages("https://t.me/Sveto4rus_bot", limit=1)[0].message

            if "Необходимо быть подписанным на канал" in text:
                print("Требуется подписка на канал, подписываемся")
                subscribe_to_channel(client, "@sveto4ch")
            else:
                company_black_list_match = extract_company_black_list(text)
                company_info_match.__setitem__('Уровень риска', company_black_list_match)
                break

        if company_info_match:
            result_df_list.append(company_info_match)

        print(f"Успешно\n")

    except Exception as e:
        print(f"\nНе удалось отправить/получить сообщение для ИНН {inn}. Ошибка: {e}\n")

result_df = pd.DataFrame(result_df_list)
result_df.to_csv(result_file_path, index=False)

print("\nПрограмма завершена.")

client.disconnect()