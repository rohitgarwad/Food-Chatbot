import mysql.connector
from mysql.connector import Error

# Connect to MySQL database
connection = mysql.connector.connect(
    host='localhost',           # Replace with your DB host
    user='root',       # Replace with your DB username
    password='root',   # Replace with your DB password
    database='pandeyji_eatery'    # Replace with your DB name
)

def insert_order_tracking(order_id: int, status: str):
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
            cursor.execute(query, (order_id, status))
            connection.commit()

    except Error as e:
        return f"Error while connecting to MySQL: {e}"

    finally:
        if connection.is_connected():
            cursor.close()

def get_total_order_price(order_id: int):
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            query = f"SELECT get_total_order_price({order_id})"
            cursor.execute(query)

            return cursor.fetchone()[0]

    except Error as e:
        connection.rollback()
        return -1

    finally:
        if connection.is_connected():
            cursor.close()

def insert_order_item(food_item: str, quantity: int, next_order_id: int):
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.callproc("insert_order_item", (food_item, quantity, next_order_id))
            connection.commit()

            return 1

    except Error as e:
        connection.rollback()
        return -1

    finally:
        if connection.is_connected():
            cursor.close()


def get_next_order_id():
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            query = "SELECT MAX(order_id) FROM orders"
            cursor.execute(query)

            result = cursor.fetchone()[0]
            if result is None:
                return 1
            else:
                return result + 1

    except Error as e:
        return f"Error while connecting to MySQL: {e}"

    finally:
        if connection.is_connected():
            cursor.close()

def get_order_status(order_id: int):
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            query = "SELECT status FROM order_tracking WHERE order_id = %s"
            cursor.execute(query, (order_id,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                return None

    except Error as e:
        return f"Error while connecting to MySQL: {e}"

    finally:
        if connection.is_connected():
            cursor.close()

def close_connection():
    try:
        if connection.is_connected():
            connection.close()
    except Error as e:
        print(e)
