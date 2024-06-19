
import pyodbc

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

def execute_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
 
    return cursor

def execute_non_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit() 
    return cursor

def fetch_and_print_results(cursor):
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def return_table_obj(cursor):
    return cursor.fetchall()

def clear_db(cursor):
    mas = []

def insert_db(command):
    con = connect_to_db()
    execute_non_query(con, command)

def retrieve_keys(conn):
    query = "SELECT key_value FROM key_storage"
    cursor = execute_query(conn, query)
    keys = return_table_obj(cursor)
    return [key[0] for key in keys]  # Повертаємо лише значення ключів

def clear_keys(conn):
    query = "DELETE FROM key_storage"
    execute_query(conn, query)
    conn.commit()

def alter_db(command):
    con = connect_to_db()
    execute_non_query(con, command)

def get_table(command):
    con = connect_to_db()
    cursor = execute_query(con, command)
    return cursor.fetchall()

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

# Підключення до бази даних
#conn = connect_to_db()

# Приклад SQL-запиту
#query = 'SELECT * FROM Страви'

# Виконання запиту та отримання результатів
#cursor = execute_query(conn, query)

# Виведення результатів
#fetch_and_print_results(cursor)

# Закриття підключення та курсора
#cursor.close()
#conn.close()
