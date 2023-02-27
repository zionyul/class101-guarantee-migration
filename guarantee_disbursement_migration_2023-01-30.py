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
relative_path = os.path.join(current_dir, '../guarantee_migration_result_staging_2023-01-31.csv')
print(relative_path)

# -f 값을 읽어서, 파일을 선택한다.
file_map = {'local': 'guarantee_migration_result_development_2023-02-27.csv',
           'development': 'guarantee_migration_result_development_2023-02-27.csv',
           'staging': 'guarantee_migration_result_staging_2023-02-27.csv',
           'production': 'guarantee_migration_result_production_2023-02-27.csv'}

file_name = file_map.get(running_env)
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

def get_remaining_guarantee(storeId):
    remaining_guarantee_mapping = {
        '63464b9c7d98bc00154ddff4': 2400,
        '63c5da9c4154fa0016ddbec9': 700,
        '603fa00d029fd2000e0532d1': 12000000,
        '604783fbb51f020015383f48': 8000000,
        '6232d4947456cc000d211875': 45000000,
        '628382e8e89e480015df24e8': 80000000,
        '61e7953a4cb71000148b7b5f': 18000000,
        '632183665435f6000f7b28e2': 6000000,
        '5f16b35e7b86c30de421f953': 4500000,
        '61fddf5a47fb97001454d023': 12000000,
        '62ce0a634c9b9e000e37e657': 7500000,
        '60ff7ec554499f000d8967b0': 4000000,
        '6090bd5c93cea9000eac2ef5': 20000000,
        '60f1308bc69381001510783a': 1500000,
        '5e5382a0169295408735b8e4': 4000000,
        '5f55d3163d49e3000cbefc09': 8000000
    }
    return remaining_guarantee_mapping.get(storeId, row['remaining_guarantee'])

for row in data:
    storeId = row['store_id']
    guaranteeStartDate = row['guarantee_start_date']
    # if datetime.strptime(guaranteeStartDate, "%Y-%m-%d %H:%M:%S") > datetime(2022, 12, 1, 00, 00, 00):
    print(guaranteeStartDate)
    
    # fixed_guarantee = 'fixed_guarantee_per_month'

    if storeId in ( '63464b9c7d98bc00154ddff4', 
                    '63c5da9c4154fa0016ddbec9', 
                    '603fa00d029fd2000e0532d1',
                    '604783fbb51f020015383f48',
                    '6232d4947456cc000d211875', 
                    '628382e8e89e480015df24e8', 
                    '61e7953a4cb71000148b7b5f', 
                    '632183665435f6000f7b28e2',
                    '5f16b35e7b86c30de421f953',
                    '61fddf5a47fb97001454d023', 
                    '62ce0a634c9b9e000e37e657',
                    '60ff7ec554499f000d8967b0',
                    '6090bd5c93cea9000eac2ef5', 
                    '60f1308bc69381001510783a',
                    '5e5382a0169295408735b8e4',
                    '5f55d3163d49e3000cbefc09'):
        remainingGuarantee = get_remaining_guarantee(storeId)
    else:
        remainingGuarantee = row['remaining_guarantee']

    print(remainingGuarantee)

    # if storeId == '63464b9c7d98bc00154ddff4':
    #     remainingGuarantee = 2400
    # elif storeId == '63c5da9c4154fa0016ddbec9':
    #     remainingGuarantee = 700
    # else
    #     remainingGuarantee = row['remaining_guarantee']

    payload = {
    "disbursementType": "GUARANTEE",
    "exchangeMonth": "202211",
    "money": {
                "amount": remainingGuarantee,
                "currency": row['guarantee_currency']
             },
    "actionType": "DISBURSEMENT",
    "storeId": row['store_id'],
    "externalToken": row['guarantee_code'],
    "registerBy": "DAVID"
    }
 
    # def check_guarantee_validity(remainingGuarantee, guaranteeStartDate):
    
    if float(remainingGuarantee) > 0.00 and not (datetime.strptime(guaranteeStartDate, "%Y-%m-%d %H:%M:%S") > datetime(2022, 12, 1, 0, 0, 0)):
        print(payload)
        response_data = post_request(url, payload)


    # if float(remainingGuarantee) > 0.00 && !(datetime.strptime(guaranteeStartDate, "%Y-%m-%d %H:%M:%S") > datetime(2022, 12, 1, 00, 00, 00)):
    #     print(payload)

    # if float(remainingGuarantee) > 0.00:
    #     response_data = post_request(url, payload)

    # print(response_data)
    # time.sleep(1)
    time.sleep(0.2)  # pauses the program for 5 seconds

