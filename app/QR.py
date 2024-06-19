import pyodbc
import qrcode
import cv2
from cryptography.fernet import Fernet
from PIL import Image
from DB import connect_to_db, execute_non_query, execute_query, store_key, retrieve_unused_keys, mark_key_as_used

"""
# Функції для підключення до бази даних та роботи з нею
def connect_to_db():
    # Параметри підключення
    server = 'GPC'
    database = 'RestaurantDB'
    username = 'Kyrylo'
    password = 'MsSQL_sec_con_2024#'

    conn_str = (
        f'DRIVER=ODBC Driver 17 for SQL Server;'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        #f'Encrypt=yes;'  
    )
    conn = pyodbc.connect(conn_str)
    return conn

def execute_non_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()  # Коміт для запитів, які змінюють дані
    return cursor

def execute_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor


def store_key(conn, key_value):
    query = f"INSERT INTO key_storage (key_value, used) VALUES ('{key_value}', 0)"
    execute_non_query(conn, query)

def retrieve_unused_keys(conn):
    query = "SELECT key_value FROM key_storage WHERE used = 0"
    cursor = execute_query(conn, query)
    keys = cursor.fetchall()
    return [key[0] for key in keys]

def mark_key_as_used(conn, key_value):
    query = f"UPDATE key_storage SET used = 1 WHERE key_value = '{key_value}'"
    execute_non_query(conn, query)
"""


# Функції для шифрування та дешифрування повідомлень з використанням ключів
def encrypt_message(message, key):
    cipher_suite = Fernet(key)
    encrypted_message = cipher_suite.encrypt(message.encode())

    con = connect_to_db()
    cursor = execute_query(con, f"SELECT id FROM key_storage WHERE key_value = '{key}'")

    # Отримання результату
    result = cursor.fetchall()
    #print(result[0][0])
    final_message = encrypted_message.decode() +"|"+ str(result[0][0])


    return final_message

def decrypt_message(encrypted_message, key):
    cipher_suite = Fernet(key)
    decrypted_message = cipher_suite.decrypt(encrypted_message.encode())
    return decrypted_message.decode()

# Функції для створення та зчитування QR-кодів
def create_qr(message, save_path):
    qr = qrcode.make(message)
    qr.save(save_path)

def read_qr(image_path):
    img = cv2.imread(image_path)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data


def get_protect_QR(message):
    conn = connect_to_db()

    # Збереження ключа у базі даних
    #key = Fernet.generate_key()
    #store_key(conn, key.decode())


    # Отримання невикористаних ключів з бази даних
    keys = retrieve_unused_keys(conn)

    if not keys:
        key = Fernet.generate_key()
        store_key(conn, key.decode())
        keys = retrieve_unused_keys(conn)

    # Вибираємо перший невикористаний ключ
    key_to_use = keys[0]

    # Шифрування повідомлення за допомогою обраного ключа
    encrypted_message = encrypt_message(message, key_to_use)
    print("Після шифрування:", encrypted_message)
    # Створення QR-коду з зашифрованим повідомленням
    qr_save_path = "encrypted_qr.png"
    create_qr(encrypted_message, qr_save_path)
    #print("try")
    conn.close()

def decode_QR(): # проблема отримання ключа
    conn = connect_to_db()

    qr_save_path = "encrypted_qr.png"
    QR_message = read_qr(qr_save_path)

    message_id = QR_message.split('|')

    try:
        cursor = execute_query(conn, f"SELECT key_value, used FROM key_storage WHERE id = '{message_id[1]}'")
    except:
        return ''

    result = cursor.fetchall()

    if not result or result[0][1]==1: # блокування після першого використання
        conn.close()
        return ''


    key_to_use = result[0][0]

    # Зчитування та дешифрування повідомлення з QR-коду
    decrypted_data = decrypt_message(message_id[0], key_to_use)
    #print("Дешифроване повідомлення:", decrypted_data)

    # Позначення ключа як використаного у базі даних
    mark_key_as_used(conn, key_to_use)

    # Закриття з'єднання з базою даних
    conn.close()
    return decrypted_data
"""
# Підключення до бази даних
conn = connect_to_db()

# Збереження ключа у базі даних
key = Fernet.generate_key()
store_key(conn, key.decode())
conn.close()



conn = connect_to_db()
# Отримання невикористаних ключів з бази даних
keys = retrieve_unused_keys(conn)

if not keys:
    print("Немає доступних ключів у базі даних.")
else:

    # Вибираємо перший невикористаний ключ
    key_to_use = keys[0]

    # Шифрування повідомлення за допомогою обраного ключа
    message = "Секретне повідомлення"
    encrypted_message = encrypt_message(message, key_to_use)

    # Створення QR-коду з зашифрованим повідомленням
    qr_save_path = "encrypted_qr.png"
    create_qr(encrypted_message, qr_save_path)
conn.close()




conn = connect_to_db()


# Зчитування та дешифрування повідомлення з QR-коду
decrypted_data = decrypt_message(read_qr(qr_save_path), key_to_use)
print("Дешифроване повідомлення:", decrypted_data)

# Позначення ключа як використаного у базі даних
mark_key_as_used(conn, key_to_use)

# Закриття з'єднання з базою даних
conn.close()
"""