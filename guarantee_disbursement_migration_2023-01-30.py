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
url_map = {'local': 'http://localhost:8080/api/v1/disbursement',
           'development': 'http://dev-payout.private.class101.net/api/v1/disbursement',
           'staging': 'http://staging-payout.private.class101.net/api/v1/disbursement',
           'production': 'http://payout.private.class101.net/api/v1/disbursement'}

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

def extract_contract_type(guarantee_contract_name):
    contract_type_map = {
        "클래스 계약": "KLASS_CREATOR",
        "구독 동의 계약": "SUBSCRIPTION_CREATOR",
        "매입 클래스 계약": "PRIVATE_BRAND"
    }
    return contract_type_map.get(guarantee_contract_name, None)

for row in data:
    storeId = row['store_id']
    guaranteeStartDate = row['guarantee_start_date']
    if datetime.strptime(guaranteeStartDate, "%Y-%m-%d %H:%M:%S") > datetime(2022, 12, 1, 00, 00, 00):
        print(guaranteeStartDate)

    fixed_guarantee = 'fixed_guarantee_per_month'

    if storeId in ('63464b9c7d98bc00154ddff4', '63c5da9c4154fa0016ddbec9'):
        remainingGuarantee = row.get(fixed_guarantee)
    else:
        remainingGuarantee = row['remaining_guarantee']

    # if storeId == '63464b9c7d98bc00154ddff4':
    #     remainingGuarantee = row['fixed_guarantee_per_month']
    # elif storeId == '63c5da9c4154fa0016ddbec9':
    #     remainingGuarantee = row['fixed_guarantee_per_month']
    # else
    #     remainingGuarantee = row['remaining_guarantee']

    payload = {
    "disbursementType": "GUARANTEE",
    "money": {
                "amount": remainingGuarantee,
                "currency": row['guarantee_currency']
             },
    "actionType": "DISBURSEMENT",
    "storeId": row['store_id'],
    "externalToken": row['guarantee_code'],
    "registerBy": "DAVID"
    }
    if datetime.strptime(guaranteeStartDate, "%Y-%m-%d %H:%M:%S") > datetime(2022, 12, 1, 00, 00, 00):
        print(payload)

    # if float(remainingGuarantee) > 0.00:
    #     response_data = post_request(url, payload)

    # print(response_data)
    # time.sleep(1)
    time.sleep(0.2)  # pauses the program for 5 seconds

