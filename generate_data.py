import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# 시드 설정 (재현성)
np.random.seed(42)
random.seed(42)

# 한국 이름 데이터
first_names = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권']
last_names = ['민준', '서연', '지호', '은지', '준호', '혜진', '현준', '수진', '태희', '유미', '동욱', '세미', '준영', '지연', '민수']

def generate_customer_names(n):
    return [random.choice(first_names) + random.choice(last_names) for _ in range(n)]

def generate_customers(n=1000):
    """고객 정보 생성"""
    data = {
        '고객ID': [f'CUST{str(i).zfill(5)}' for i in range(1, n+1)],
        '고객명': generate_customer_names(n),
        '연락처': [f'010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}' for _ in range(n)],
        '이메일': [f'customer{i}@email.com' for i in range(1, n+1)],
        '가입일': [datetime(2022, 1, 1) + timedelta(days=random.randint(0, 750)) for _ in range(n)],
        '고객등급': np.random.choice(['VIP', 'Gold', 'Silver', 'Bronze'], n),
        '누적구매액': np.random.randint(100000, 5000000, n),
        '주소': [f'서울시 {random.choice(["강남구", "서초구", "송파구", "강동구", "용산구"])}' for _ in range(n)],
    }
    return pd.DataFrame(data)

def generate_products(n=50):
    """제품/서비스 정보 생성"""
    categories = ['노트북', '휴대폰', '태블릿', '액세서리', '소프트웨어', '서비스']
    data = {
        '제품ID': [f'PROD{str(i).zfill(4)}' for i in range(1, n+1)],
        '제품명': [f'{random.choice(categories)} 상품-{i}' for i in range(1, n+1)],
        '카테고리': [random.choice(categories) for _ in range(n)],
        '가격': np.random.randint(50000, 2000000, n),
        '재고': np.random.randint(0, 1000, n),
        '출시일': [datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1825)) for _ in range(n)],
    }
    return pd.DataFrame(data)

def generate_channels(n=5):
    """응대 채널 정보 생성"""
    data = {
        '채널ID': [f'CH{str(i).zfill(2)}' for i in range(1, n+1)],
        '채널명': ['전화', '이메일', '라이브채팅', '카톡', 'SNS'],
        '활성화': [True] * n,
        '운영시간': ['09:00-18:00', '24시간', '09:00-22:00', '09:00-21:00', '09:00-18:00'],
    }
    return pd.DataFrame(data)

def generate_service_records(n=5000):
    """응대 이력 생성"""
    customers = pd.read_csv('customers.csv')
    products = pd.read_csv('products.csv')

    issues = ['제품 불량', '배송 지연', '결제 오류', '반품/교환', '제품 문의', '서비스 문의',
              '가격 정보 문의', '기술 지원', '계정 문제', '프로모션 문의']
    statuses = ['해결완료', '진행중', '대기중', '미해결']
    channels = ['전화', '이메일', '라이브채팅', '카톡', 'SNS']
    agents = [f'상담원{i}' for i in range(1, 21)]

    base_date = datetime(2024, 1, 1)

    data = {
        '응대ID': [f'SVC{str(i).zfill(6)}' for i in range(1, n+1)],
        '고객ID': np.random.choice(customers['고객ID'].values, n),
        '제품ID': np.random.choice(products['제품ID'].values, n),
        '응대일시': [base_date + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23), minutes=random.randint(0, 59)) for _ in range(n)],
        '응대채널': np.random.choice(channels, n),
        '응대자': np.random.choice(agents, n),
        '문의유형': np.random.choice(issues, n),
        '상태': np.random.choice(statuses, n, p=[0.5, 0.2, 0.2, 0.1]),
        '응대시간(분)': np.random.randint(5, 120, n),
        '만족도': np.random.choice(['매우만족', '만족', '보통', '불만족', '매우불만족'], n, p=[0.3, 0.3, 0.2, 0.1, 0.1]),
        '처리완료일시': [
            base_date + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            if random.random() > 0.3 else None for _ in range(n)
        ],
        '비고': [random.choice(['', '', '', '고객 피드백 있음', '재문의 필요', '영구차단 고객', '긴급 처리']) for _ in range(n)],
    }
    return pd.DataFrame(data)

print("데이터 생성 중...")

# 고객 정보
customers = generate_customers(1000)
customers.to_csv('customers.csv', index=False, encoding='utf-8-sig')
print("[O] customers.csv 생성 완료 (1,000건)")

# 제품 정보
products = generate_products(50)
products.to_csv('products.csv', index=False, encoding='utf-8-sig')
print("[O] products.csv 생성 완료 (50건)")

# 채널 정보
channels = generate_channels(5)
channels.to_csv('channels.csv', index=False, encoding='utf-8-sig')
print("[O] channels.csv 생성 완료 (5건)")

# 응대 이력 (고객과 제품 정보 필요)
service_records = generate_service_records(5000)
service_records.to_csv('service_records.csv', index=False, encoding='utf-8-sig')
print("[O] service_records.csv 생성 완료 (5,000건)")

print("\n데이터 생성 완료!")
print("\n생성된 파일:")
print("- customers.csv: 고객 정보 (1,000건)")
print("- products.csv: 제품/서비스 정보 (50건)")
print("- channels.csv: 응대 채널 정보 (5건)")
print("- service_records.csv: 응대 이력 (5,000건)")
