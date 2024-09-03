# 3k1k_test

## 실행 방법

### 가상 환경 설정

```
python3 -m venv .venv
. .venv/bin/activate

```

### 패키지 다운로드

```
pip install -r requirements.txt
```

### DB 설정 추가

```
# config.py
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': ''
}
```

### 실행

```
locust -f "file명"
```
