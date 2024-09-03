import random
import mysql.connector
from locust import HttpUser, task, between, events
import logging
from collections import deque
from config import DB_CONFIG # DB_CONFIG 가져오기

# 전역 변수로 데이터 저장
users = deque([])
logged_in_users = set()
stores = []
menus = {}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global users, stores, menus
    print("Test is starting. Loading data from database...")
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor(dictionary=True)

    # 사용자 데이터 로드
    cursor.execute("SELECT id, email, password FROM customers ORDER BY rand() limit 100000")
    users = deque(cursor.fetchall())

    # 상점 데이터 로드
    cursor.execute("SELECT id FROM store ORDER BY rand() limit 1000")
    stores = [store['id'] for store in cursor.fetchall()]
    # print("stores: ", stores)
    
    # 메뉴 데이터 로드
    # 각 상점 별로 메뉴 dictionary 형태로 저장
    for store_id in stores:
        cursor.execute("SELECT id FROM menu WHERE store_id = %s", (store_id,))
        menus[store_id] = cursor.fetchall()
    # print("menus", menus)

    cursor.close()
    db.close()
    print("Data loading completed.")

class CartUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        self.login()

    def login(self):
        if not users:
            logging.warning("No more available users to log in.")
            return
        
        user = users.popleft()
        with self.client.post(
            "/customers/login",
            json={"email": user['email'], "password": user['password']},
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 204:
                logging.info(f"Successfully logged in as user {user['email']}")
                logged_in_users.add(user['id'])
                self.user = user
            else:
                logging.error(f"Failed to log in as user {user['email']}. Status code: {response.status_code}, {response.json()['detail']}")
                response.failure(f"Login failed with status code: {response.status_code}")

    @task
    def add_to_cart(self):
        if not hasattr(self, 'user'):
            logging.warning("User not logged in. Skipping add_to_cart.")
            return

        store_id = random.choice(stores)
        store_menus = menus[store_id]
        
        if not store_menus:
            logging.warning(f"No menus available for store {store_id}. Skipping add_to_cart.")
            return

        selected_menus = random.sample(store_menus, min(random.randint(1, 5), len(store_menus)))

        for menu in selected_menus:
            with self.client.post(
                "/cart",
                json={"menuId": menu['id']},
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    logging.info(f"Successfully added menu {menu['id']} to cart for user {self.user['email']}")
                else:
                    logging.error(f"Failed to add menu {menu['id']} to cart for user {self.user['email']}. Status code: {response.status_code}")
                    response.failure(f"Add to cart failed with status code: {response.status_code}, {response.json()['detail']}")
        
        with self.client.post(
            "/orders",
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 201:
                logging.info(f"Successfully placed an order for user {self.user['email']}")
            else:
                logging.error(f"Failed to place an order for user {self.user['email']}. Status code: {response.status_code}")
                response.failure(f"Place order failed with status code: {response.status_code}, {response.json()['detail']}")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')