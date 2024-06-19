import os
import webbrowser
import sys
import subprocess
import datetime
import voice
import vocabular
import requests
import DB
from QR import *
import re
import vosk                 #pip install vosk
import sounddevice as sd    #pip install sounddevice
import queue
import json

import threading
import matplotlib.pyplot as plt
from PIL import Image

#from Order_recognition import take_o 

model = vosk.Model('model')       # голосова модель
device = sd.default.device  = 2,6     # <--- за замовчуванням
                                      #обо -> sd.default.device = 1, 3, python -m sounddevice просмотр 
samplerate = int(sd.query_devices(device[0], 'input')['default_samplerate'])  #отримуємо частоту мікрофону
q = queue.Queue()

table_activate = False
total_order = {}
table_data = {}

def callback(indata, frames, time, status):
    '''
     Додає в чергу семпли з потоку.
     викликається щоразу при наповненні blocksize
     в sd.RawInputStream'''

    q.put(bytes(indata))

def weather():
    '''Для работы этого кода нужно зарегистрироваться на сайте
    https://openweathermap.org или переделать на ваше усмотрение под что-то другое'''
    try:
        params = {'q': 'Київ', 'units': 'metric',
                  'lang': 'uk', 'appid': vocabular.api_token}
        response = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather', params=params)
        if not response:
            raise
        w = response.json()
        voice.speaker(
            f"На вулиці {w['weather'][0]['description']} {round(w['main']['temp'])} градусів")
        print(f"На вулиці {w['weather'][0]['description']} {round(w['main']['temp'])} градусів")

    except:
        voice.speaker(
            'Сталася помилка')

def get_current_time():

    time_ = datetime.datetime.now().strftime('%H:%M:%S')
    hour, minutes, seconds = time_.split(':')
    current_time = f"Зараз {hour}:{minutes}"

    voice.speaker(current_time)
    print(current_time)

def get_current_date():

    date_ = datetime.date.today()
    year, month, day = str(date_).split('-')
    current_date = f"Зараз {vocabular.months_to_name[month]} {day}"

    voice.speaker(current_date)
    print(current_date)
    return current_date

def get_menu_list():
    con = DB.connect_to_db()
    cursor = DB.execute_query(con, f'SELECT dish_name, price, id, vegetarian FROM Dishes')
    
    menu = {row[0].replace('"', '').lower(): {'price': float(row[1]), 'id': row[2], 'vegetarian': row[3]} for row in cursor.fetchall()}

    return menu

main_menu = get_menu_list()

def check_free_tables():
    con = DB.connect_to_db()
    cursor = DB.execute_query(con, f'SELECT DISTINCT number_of_seats FROM Tables WHERE status_free = 1 ')

    sits = ''
    for row in cursor.fetchall():
        #print(row[0])
        sits += str(row[0])
        sits += ', '
    
    if not sits:
        voice.speaker('Наразі нема вільних місць')
        return

    say = f'На даний момент є вільні місця на {sits} особи'
    voice.speaker(say)
    print(say)

def check_reserv_tables():
    con = DB.connect_to_db()
    cursor = DB.execute_query(con, f'SELECT DISTINCT number_of_seats FROM Tables WHERE status_free =0 ')

    sits = ''
    for row in cursor.fetchall():
        print(row[0])
        sits += str(row[0])
        sits += ', '
    
    if not sits:
        voice.speaker('Наразі всі місця вільні')
        return

    say = f'На даний момент є зарезервовані місця на {sits} особи'
    voice.speaker(say)
    print(say)

"""
def check_tables(free):
    con = DB.connect_to_db()
    cursor = DB.execute_query(con, f'SELECT DISTINCT кількість_місць FROM Столики WHERE статус !={free} ')

    return cursor.fetchall()


def make_comand(command):
    con = DB.connect_to_db
    cursor = DB.execute_query(con, command)


    cursor.close()
    con.close()
"""

# Допоміжне
def add_to_order(order, new_order):
    for item, quantity in new_order.items():
        if item in order:
            order[item] += quantity
        else:
            order[item] = quantity

def delete_from_order(order, remove_order):
    for item, quantity in remove_order.items():
        if item in order:
            if order[item] > quantity:
                order[item] -= quantity
            else:
                del order[item]

# Допіміжна 
def create_order_string(order_dict, add = 1):
   
    # Формуємо список із фраз типу "1 борщ"
    order_list = [f"{quantity} {item}" for item, quantity in order_dict.items()]
    
    # З'єднуємо всі елементи списку в рядок із комами, крім останнього елемента
    if len(order_list) > 1:
        result_string = ", ".join(order_list[:-1]) + " і " + order_list[-1]
    else:
        result_string = order_list[0]
    
    # Додаємо початок фрази "Ви замовили"
    if add:
        return "Ви замовили " + result_string
    else:
        return "Ви видалили " + result_string

def take_order(order = None, parser = None):

    #print('table_activate2', table_activate)
    if table_activate:
        dishes, lemmatized_order = parser.parse_order(order)
        print("Замовлення:", lemmatized_order)
        print("Страви та їх кількості:", dishes)
        #print("- dishes", dishes)

        if not dishes:
            return

        add_to_order(total_order, dishes)
        ord = create_order_string(dishes)
        voice.speaker(ord)
    else:
        voice.speaker("Ви не можете отримати замовлення при реєстрації")


def get_list_str_order():
    order = ''
    for key, value in total_order.items():
        order += f'{value} {key}, '
    return order

def remove_from_order(order = None, parser = None):
    if table_activate:
        dishes, lemmatized_order = parser.parse_order(order)
        print("Замовлення:", lemmatized_order)
        print("Страви та їх кількості для видалення:", dishes)
        #print("- dishes", dishes)

        delete_from_order(total_order, dishes)

        ord = create_order_string(dishes, 0)
        voice.speaker(ord)
    else:
        print("Ви не можете отримати замовлення при реєстрації")

def get_total_cost():
    total_cost = 0
    for item, quantity in total_order.items():
        total_cost += main_menu[item]['price'] * quantity
    return total_cost

    print(get_total_cost())

def add_order():
    print("table_data", table_data)
    command = f"SELECT * FROM Orders where id_table = {table_data['id']} and status_order = 1"

    if not DB.get_table(command):
        DB.insert_db(f"INSERT INTO Orders VALUES ({table_data['id']}, GETDATE(), Null, 1, {get_total_cost()})")
    else:
        DB.insert_db(f"UPDATE Orders SET total_sum = total_sum+{get_total_cost()} WHERE id_table = {table_data['id']} and status_order = 1")

    for item, quantity in total_order.items():
        DB.insert_db(f"INSERT INTO Order_details VALUES ((SELECT id from Orders WHERE id_table = {table_data['id']} and status_order=1), {main_menu[str(item)]['id']},{quantity})")


def confirm_order():
    '''
    Підтвердження замовлення
    '''
    conf_order_str = f"Ви підтверджуєте замовлення на {get_list_str_order()} ? з вас буде {get_total_cost()}"
    print(conf_order_str)
    voice.speaker(conf_order_str)

    # Чекаємо відповіді користувача
    with sd.RawInputStream(samplerate=samplerate, blocksize = 24000, device=device[0], dtype='int16',
                            channels=1, callback=callback):

        rec = vosk.KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                data = json.loads(rec.Result())['text']
                if data == "так":
                    # Обробляємо підтвердження
                    voice.speaker("Замовлення підтверджене")
                    print("Замовлення підтверджене")
                    add_order()
                    global total_order
                    total_order.clear()
                    break

                elif data == "ні":
                    voice.speaker("Відміна підтвердження")
                    print("Відміна підтвердження")
                    break
                else:
                    print("Не можу розпізнати відповідь")
                    

def end_session():
    global table_activate
    if not table_activate:
        voice.speaker("Сесія ще не починалась?")

    voice.speaker("Ви підтверджуєте закінчення сесії?")

    with sd.RawInputStream(samplerate=samplerate, blocksize = 24000, device=device[0], dtype='int16',
                            channels=1, callback=callback):

        rec = vosk.KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                data = json.loads(rec.Result())['text']
                if data == "так":
                    # Обробляємо підтвердження
                    print("Користувач підтвердив ЗАКІНЧЕННЯ СЕСІЇ")

                    voice.speaker("Сесію закінчено, дякую, приходьте ще")

                    DB.insert_db(f"UPDATE Orders SET time_end = GETDATE(), status_order = 0 WHERE id_table = {table_data['id']} and status_order = 1")
                    DB.insert_db(f"UPDATE tables SET status_free = 1 WHERE id = {table_data['id']};")

                    table_activate = False
                    total_order.clear()
                    table_data.clear()
                    break

                elif data == "ні":
                    print("Користувач скасував ЗАКІНЧЕННЯ СЕСІЇ")
                    voice.speaker("Закінчення сесії скасовано")
                    break
                else:
                    voice.speaker("Не можу розпізнати відповідь")


def show_image(file_path, name = ''):
    # Завантаження зображення за допомогою Pillow
    try:
        img = Image.open(file_path)
    except Exception as e:
        print(f"Не вдалося відкрити файл: {e}")
        return

    # Відображення зображення за допомогою matplotlib
    fig, ax = plt.subplots()
    ax.imshow(img)
    ax.set_title(name)
    ax.axis('off')

    plt.show(block=False)  # Відкрити вікно з зображенням без блокування

    while plt.fignum_exists(fig.number):
        plt.pause(0.1)  # Пауза для оновлення вікна

def show_menu_list():


    file_path = os.path.abspath("Menu.png")

    # Перевірка, чи існує файл
    if not os.path.isfile(file_path):
        print(f"Файл {file_path} не знайдено.")
    else:
        # Запуск показу зображення в окремому потоці
        thread = threading.Thread(target=show_image, args=(file_path,'Меню',))
        thread.start()
    say = 'Перейдіть по QR-коду для перегляду меню'
    voice.speaker(say)
    print(say)

def show_QR_code():


    file_path = os.path.abspath("encrypted_qr.png")

    # Перевірка, чи існує файл
    if not os.path.isfile(file_path):
        print(f"Файл {file_path} не знайдено.")
    else:
        # Запуск показу зображення в окремому потоці
        thread = threading.Thread(target=show_image, args=(file_path,))
        thread.start()


def check_order():
    
    if not total_order:
        voice.speaker(f'Ви ще нічого не замовили')
        return

    order = get_list_str_order()
    
    pr_order = f'Ви замовили {order}'
    print(pr_order)
    voice.speaker(pr_order)

def skip():
    pass

# Допоміжне
def extract_person_count(sentence):
    # Шаблон для знаходження чисел, перед якими можуть стояти різні слова
    pattern = r'(\d+)\s+\w*'

    matches = re.findall(pattern, sentence)
    if matches:
        return int(matches[0])  # Повертаємо перше знайдене число
    return None

# Допоміжне
def check_tables_mas(free):
    con = DB.connect_to_db()
    cursor = DB.execute_query(con, f'SELECT DISTINCT number_of_seats FROM Tables WHERE status_free ={free} ')

    free_sits = []
    for row in cursor.fetchall():
        free_sits.append(row[0])

    con.close()

    return free_sits

def table_access_get(order = None, parser = None):
    #print('order', order, 'parser', parser)

    persons = extract_person_count(order)
    if persons in check_tables_mas(1):
        con = DB.connect_to_db()
        cursor = DB.execute_query(con, f'SELECT TOP 1 * FROM Tables WHERE number_of_seats = {persons} and status_free = 1')

        result = cursor.fetchall()
        inf = f'{result[0][0]}|{result[0][1]}|{result[0][2]}|{result[0][3]}'
        get_protect_QR(inf)
        show_QR_code()
        voice.speaker(f'Збережіть QR код, це буде ваш ключ доступу')

    else:
        voice.speaker(f'Нема наявних місць для {persons} осіб')

def table_access_pass():
    global table_activate, table_data
    message = decode_QR();
    print('Після дешифрування:', message)
    if not message:
        voice.speaker(f'Ваш QR код не є дійсним')
        print(f'Ваш QR код не є дійсним')
    else:
        voice.speaker(f'Ласкаво просимо')
        table_activate = True
        values = message.split("|")

        table_data = {
            "id": int(values[0]),
            "table_number": int(values[1]),
            "number_of_seats": int(values[2]),
            "status_free": values[3] == "True"  # Перетворюємо рядок у булеве значення
            }
        DB.alter_db(f"UPDATE Tables SET status_free = 0 WHERE id = {table_data['id']};")

        #print('table_activate1', table_activate)


