import csv
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

# -f 값을 읽어서, 파일을 선택한다.
file_map = {'USD': 'GUARANTEE_FINAIL_2022-12_USD.csv',
            'KRW': 'GUARANTEE_FINAIL_2022-12_KRW.csv',
            'JPY': 'GUARANTEE_FINAIL_2022-12_JPY.csv'}

file_name = file_map.get(migration_file)
if file_name:
    data = read_csv(file_name)
else:
    data = None

# -c 값을 읽어서, 서버를 선택한다.
url_map = {'local': 'http://localhost:8080/api/v1/guarantee',
           'development': 'http://dev-payout.private.class101.net/api/v1/guarantee',
           'staging': 'http://staging-payout.private.class101.net/api/v1/guarantee',
           'production': 'http://payout.private.class101.net/api/v1/guarantee'}

url = url_map.get(running_env)
if url is None:
    url = None

def post_request(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f'Request failed with status code {response.status_code}')

def change_utc_timezone(date_string, is_subtract):
    formats = {7: "%Y-%m", 6: "%Y-%m", 10: "%Y-%m-%d"}
    date_format = formats.get(len(date_string))
    if not date_format:
        return ""
    date_object = datetime.strptime(date_string, date_format)
    if is_subtract:
        date_object = subtract_one_month(date_object)
    return convert_to_utc(date_object)

def convert_to_utc(date_object):
    tz = pytz.timezone("Asia/Seoul")
    zoned_datetime = tz.localize(date_object)
    utc_datetime = zoned_datetime.astimezone(pytz.UTC)
    return utc_datetime.isoformat()

def subtract_one_month(date):
    print(date)
    return date + relativedelta(months=-1)
    

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
    # 개런티 계약 형태
    guaranteeContractType = extract_contract_type(row['guaranteeContractType'])
    # 개런티 금액 총액
    # if row['guaranteeTotal']:
        # guaranteeTotalAmount = extract_numeric_amount(row['guaranteeTotal'])
    # else:
    guaranteeTotalAmount = extract_numeric_amount(row['guaranteeTotalKlass']) + extract_numeric_amount(row['guaranteeTotalSubscription'])
    # 잔여 개런티 금액
    # if row['remainingGuarantee']:
    #     remainingGuarantee = extract_numeric_amount(row['remainingGuarantee'])
    # else:
    remainingGuarantee = extract_numeric_amount(row['remainingGuaranteeKlass']) + extract_numeric_amount(row['remainingGuaranteeSubscription'])
    # 월별 고정 개런티 지급 금액
    if row['fixedGuaranteePerMonth']:
        fixedGuaranteePerMonth = extract_numeric_amount(row['fixedGuaranteePerMonth'])
    else:
        fixedGuaranteePerMonth = guaranteeTotalAmount
    # 개런티 지급 시작월
    guaranteeStartDate = row['guaranteeStartDate']

    if guaranteeStartDate:
        guaranteeStartDate = change_utc_timezone(guaranteeStartDate, 1)
    else:
        guaranteeStartDate = '2022-11-30T15:00:00.000Z'

    # if row['guaranteeStartDate']:
    #     guaranteeStartDate = change_utc_timezone(row['guaranteeStartDate'])
    #     guaranteeStartDate = subtract_one_month(guaranteeStartDate)
    # else:
    #     guaranteeStartDate = '2022-11-30T15:00:00.000Z'
    # 개런티 지급 종료월
    guaranteeEndDate = row['guaranteeEndDate']

    if guaranteeEndDate:
        guaranteeEndDate = change_utc_timezone(guaranteeEndDate, 1)
    else:
        guaranteeEndDate = '2022-11-30T15:00:00.000Z'

    # if row['guaranteeEndDate']:
    #     guaranteeEndDate = change_utc_timezone(row['guaranteeEndDate'])
    #     guaranteeEndDate = subtract_one_month(guaranteeEndDate)
    # else:
    #     guaranteeEndDate = '2022-11-30T15:00:00.000Z'

    print(guaranteeTotalAmount)
    print(remainingGuarantee)
    print(fixedGuaranteePerMonth)
    print(guaranteeStartDate)
    print(guaranteeEndDate)
    # 월별 최대 차감 금액
    maxDeductionPerMonth = extract_numeric_amount(row['maxDeductionPerMonth'])
    # 개런티 차감 시작월
    if row['deductionStartDate'] != 'null':
        deductionStartDate = change_utc_timezone(row['deductionStartDate'], 0)
    else:
        deductionStartDate = ''
    # 개런티 차감 종료월
    if row['deductionEndDate'] != 'null':
        deductionEndDate = change_utc_timezone(row['deductionEndDate'], 0)
    else:
        deductionEndDate = ''
    # payload = {
        # 'name': row['개런티 ID'],
        # 'age': row['개런티 코드'],
        # 'address': row['Store ID']
    # }
    payload = {
    'guaranteeContractType': guaranteeContractType,
    'guaranteePayType': 'MONTHLY_FIXED',
    'guaranteeTotal': guaranteeTotalAmount,
    'remainingGuarantee': remainingGuarantee,
    'guaranteeCurrency': row['currency'],
    'fixedGuaranteePerMonth': fixedGuaranteePerMonth,
    'guaranteeStartDate': guaranteeStartDate,
    'guaranteeEndDate': guaranteeEndDate,
    'maxDeductionPerMonth': maxDeductionPerMonth,
    'deductionStartDate': deductionStartDate,
    'deductionEndDate': deductionEndDate,
    'storeId': row['storeId'],
    'klassId': row['klassId'],
    'guaranteeMemo': row['guaranteeMemo']
    }
    print(payload)

    # url = 'http://localhost:8080/api/v1/guarantee'
    # url = 'http://dev-payout.private.class101.net/api/v1/guarantee'
    
# if running_env == 'local':
#     url = 'http://localhost:8080/api/v1/guarantee'
# elif running_env == 'development':
#     url = 'http://dev-payout.private.class101.net/api/v1/guarantee'
# elif running_env == 'staging':
#     url = 'http://staging-payout.private.class101.net/api/v1/guarantee'
# elif running_env == 'production':  
#     url = 'http://payout.private.class101.net/api/v1/guarantee'
# else:
    # data = None

    response_data = post_request(url, payload)
    print(response_data)
    # time.sleep(1)
    time.sleep(0.2)  # pauses the program for 5 seconds

