import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG # DB_CONFIG 가져오기

fake = Faker('ko_KR')

# 설정
NUM_CUSTOMERS = 1000000
NUM_VENDORS = 250000
STORES_PER_VENDOR = 2
MENU_CATEGORIES_PER_STORE = 3
MENUS_PER_CATEGORY = 5
BATCH_SIZE = 100000  # 1천만 개씩 트랜잭션 처리

# 유틸리티 함수
def generate_uuid():
    return uuid.uuid4()

def generate_phone():
    return f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

# MySQL 연결 및 커서 생성 함수
def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# 데이터 삽입 함수
def insert_data(connection, query, data):
    cursor = connection.cursor()
    try:
        cursor.executemany(query, data)
        connection.commit()
    except Error as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        cursor.close()

# 데이터 생성 및 삽입 함수
def generate_and_insert_pay_accounts(connection):
    query = "INSERT INTO pay_account (id, balance) VALUES (%s, %s)"
    batch = []
    for i in range(1, NUM_CUSTOMERS + NUM_VENDORS + 1):
        batch.append((i, random.randint(0, 1000000)))
        if len(batch) == BATCH_SIZE:
            insert_data(connection, query, batch)
            batch = []
    if batch:
        insert_data(connection, query, batch)

def generate_and_insert_customers(connection):
    query = "INSERT INTO customers (id, password, phone, name, email, pay_account_id) VALUES (%s, %s, %s, %s, %s, %s)"
    batch = []
    for i in range(NUM_CUSTOMERS):
        uuid1 = generate_uuid()
        batch.append((
            uuid1.bytes,
            fake.password(),
            generate_phone(),
            fake.name(),
            f"{uuid1}@gmail.com",
            i + 1
        ))
        if len(batch) == BATCH_SIZE:
            insert_data(connection, query, batch)
            batch = []
    if batch:
        insert_data(connection, query, batch)

def generate_and_insert_vendors(connection):
    query = "INSERT INTO vendor (id, password, phone, name, email, pay_account_id) VALUES (%s, %s, %s, %s, %s, %s)"
    batch = []
    for i in range(NUM_VENDORS):
        uuid1 = generate_uuid()
        batch.append((
            uuid1.bytes,
            fake.password(),
            generate_phone(),
            fake.company(),
            f"{uuid1}@gmail.com",
            NUM_CUSTOMERS + i + 1
        ))
        if len(batch) == BATCH_SIZE:
            insert_data(connection, query, batch)
            batch = []
    if batch:
        insert_data(connection, query, batch)

# store_category 생성 및 삽입 함수 추가
def generate_and_insert_store_categories(connection):
    query = "INSERT INTO store_category (id, name) VALUES (%s, %s)"
    store_categories = ['한식', '중식', '일식', '양식', '분식', '카페', '패스트푸드']
    data = [(i+1, category) for i, category in enumerate(store_categories)]
    insert_data(connection, query, data)
    return len(store_categories)

def generate_and_insert_stores(connection, num_categories):
    query = "INSERT INTO store (id, vendor_id, name, district, phone_number, start_hour, start_minute, end_hour, end_minute, min_order_price, store_category_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM vendor")
    vendor_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    data = [
        (i + 1, vendor_ids[i // STORES_PER_VENDOR], fake.company(), fake.city(), generate_phone(),
         random.randint(0, 12), random.choice([0, 30]), random.randint(13, 23), random.choice([0, 30]),
         random.choice([8000, 10000, 12000, 15000]), random.randint(1, num_categories))
        for i in range(NUM_VENDORS * STORES_PER_VENDOR)
    ]
    insert_data(connection, query, data)

def generate_and_insert_menu_categories(connection):
    query = "INSERT INTO menu_category (id, store_id, name) VALUES (%s, %s, %s)"
    
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM store")
    store_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    batch = []
    category_id = 1
    for store_id in store_ids:
        for _ in range(MENU_CATEGORIES_PER_STORE):
            batch.append((
                category_id,
                store_id,
                str(uuid.uuid4())
            ))
            category_id += 1
            if len(batch) == BATCH_SIZE:
                insert_data(connection, query, batch)
                batch = []
    if batch:
        insert_data(connection, query, batch)

def generate_and_insert_menus(connection):
    query = "INSERT INTO menu (id, menu_category_id, store_id, name, price, stock_count, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    menu_items = [
        "불고기", "비빔밥", "김치찌개", "된장찌개", "삼겹살", "냉면", "떡볶이", "김밥",
        "짜장면", "짬뽕", "탕수육", "마파두부", "깐풍기", "볶음밥",
        "초밥", "라멘", "돈카츠", "우동", "규동",
        "파스타", "피자", "스테이크", "샐러드", "햄버거"
    ]
    
    cursor = connection.cursor()
    cursor.execute("SELECT id, store_id FROM menu_category")
    categories = cursor.fetchall()
    cursor.close()

    batch = []
    menu_id = 1
    for category_id, store_id in categories:
        for _ in range(MENUS_PER_CATEGORY):
            batch.append((
                menu_id,
                category_id,
                store_id,
                random.choice(menu_items),
                random.randint(5000, 30000),
                random.randint(0, 100),
                fake.image_url()
            ))
            menu_id += 1
            if len(batch) == BATCH_SIZE:
                insert_data(connection, query, batch)
                batch = []
    if batch:
        insert_data(connection, query, batch)

# 메인 실행
if __name__ == "__main__":
    connection = get_connection()
    if connection is not None:
        print("PayAccount 생성 중...")
        generate_and_insert_pay_accounts(connection)

        print("Customer 생성 중...")
        generate_and_insert_customers(connection)

        print("Vendor 생성 중...")
        generate_and_insert_vendors(connection)

        print("Store Category 생성 중...")
        num_categories = generate_and_insert_store_categories(connection)

        print("Store 생성 중...")
        generate_and_insert_stores(connection, num_categories)

        print("MenuCategory 생성 중...")
        generate_and_insert_menu_categories(connection)

        print("Menu 생성 중...")
        generate_and_insert_menus(connection)

        connection.close()
        print("데이터 삽입이 완료되었습니다.")
    else:
        print("데이터베이스 연결에 실패했습니다.")