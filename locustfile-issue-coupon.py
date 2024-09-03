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
coupon_id = ""

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global users, stores, menus, coupon_id
    print("Test is starting. Loading data from database...")
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor(dictionary=True)

    # 사용자 데이터 로드
    cursor.execute("SELECT id, email, password FROM customers ORDER BY rand() limit 10000")
    users = deque(cursor.fetchall())

    # 쿠폰 로드
    cursor.execute("SELECT id FROM coupons WHERE id = 3 limit 1")
    coupon_id = cursor.fetchone()['id']

    cursor.close()
    db.close()
    print("Data loading completed.")

class CouponUser(HttpUser):
    wait_time = between(1, 3)
    users = []
    coupon_id = None

    def on_start(self):
        self.login()

    def login(self):
        if not users:
            logging.error("No users available. User creation might have failed.")
            return

        user = users.popleft()
        login_data = {
            "email": user["email"],
            "password": user["password"]
        }
        with self.client.post("/customers/login", json=login_data, catch_response=True) as response:
            if response.status_code == 204:
                response.success()
                logging.info(f"Login successful for user: {user['email']}")
            else:
                response.failure(f"Login failed: {response.status_code}, {response.text}")
                logging.error(f"Login failed for user {user['email']}: {response.status_code}, {response.text}")

    @task
    def issue_coupon(self):
        global coupon_id
        if not coupon_id:
            logging.error("No coupon available for issuing")
            return

        with self.client.post(f"/coupons/{coupon_id}/issue", catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                logging.info("Coupon issued successfully")
            elif response.status_code == 400:
                response.failure(f"Failed to issue coupon: {response.text}")
                logging.warning(f"Failed to issue coupon: {response.text}")
            else:
                response.failure(f"Unexpected response: {response.status_code}, {response.text}")
                logging.error(f"Unexpected response when issuing coupon: {response.status_code}, {response.text}")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')