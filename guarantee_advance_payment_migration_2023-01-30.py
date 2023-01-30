import csv
import requests
from datetime import datetime
import pytz
import time
import getopt
import sys

opts, args = getopt.getopt(sys.argv[1:], "f:c:")

migration_file = None
running_env = None

for opt, arg in opts:
    if opt == '-f':
        migration_file = arg
    elif opt == '-c':
        running_env = arg

print(migration_file)
print(running_env)

def read_csv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        return list(reader)

import os

# 현재 디렉토리의 상대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))

# 다른 디렉토리의 상대 경로
relative_path = os.path.join(current_dir, '../guarantee_migration_result_2023-01-26.csv')
print(relative_path)

# -f 값을 읽어서, 파일을 선택한다.
file_map = {'USD': relative_path,
            'KRW': 'guarantee_migration_result_2023-01-26.csv',
            'JPY': 'guarantee_migration_result_2023-01-26.csv'}

file_name = file_map.get(migration_file)
if file_name:
    data = read_csv(file_name)
else:
    data = None

# -c 값을 읽어서, 서버를 선택한다.
url_map = {'local': 'http://localhost:8080/api/v1/advance-payment',
           'development': 'http://dev-payout.private.class101.net/api/v1/advance-payment',
           'staging': 'http://staging-payout.private.class101.net/api/v1/advance-payment',
           'production': 'http://payout.private.class101.net/api/v1/advance-payment'}

url = url_map.get(running_env)
if url is None:
    url = None

def post_request(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f'Request failed with status code {response.status_code}')

def change_utc_timezone(date_string):
    date_length = len(date_string)
    # print(date_length)
    if date_length == 7:
        date_object = datetime.strptime(date_string, "%Y-%m")
    elif date_length == 6:
        date_object = datetime.strptime(date_string, "%Y-%m")
    elif date_length == 10:
        date_object = datetime.strptime(date_string, "%Y-%m-%d")
    else:
        return ''

    # datetime 객체를 timezone을 가진 datetime 객체로 변환
    tz = pytz.timezone('Asia/Seoul')
    zoned_datetime = tz.localize(date_object)

    # UTC timezone으로 변환
    utc_datetime = zoned_datetime.astimezone(pytz.UTC)
    return utc_datetime.isoformat()

def extract_numeric_amount(dollar_amount):
    numeric_amount = dollar_amount.replace("$", "").replace("₩", "").replace("¥", "").replace(",", "").replace(" ", "")
    return numeric_amount

for row in data:
    payload = {
    "guaranteeId": row['guarantee_id'],
    "amount": {
                "amount": row['remaining_guarantee'],
                "currency": row['guarantee_currency']
             },
    }
    print(payload)

    response_data = post_request(url, payload)
    print(response_data)
    # time.sleep(1)
    time.sleep(0.2)  # pauses the program for 5 seconds

