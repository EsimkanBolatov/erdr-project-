import requests
import json
import random

# Адрес вашего локального API
URL = "http://127.0.0.1:8000/api/external/receive_data"

# Тестовые данные (3 разных кейса)
test_cases = [
    # Кейс 1: Как на скриншоте (Антифрод)
    {
        "kui_number": "263100030000001",
        "reg_organ": "19310003",
        "district": "Заводской район",
        "reg_date": "13.01.2026 16:33",
        "event_description": "Банк остановил транзакцию системой Антифрод в связи с подозрительным переводом. Клиент подтверждает, что не совершал операцию.",
        "military_unit": "",
        "coupon_number": "",
        "coupon_date": "",
        "field_5_1": "против собственности",
        "field_5_2": "",
        "field_5_3": "Нет",
        "field_5_4": "Нет",
        "field_5_5": "Нет",
        "field_5_6": "Да", # Интернет-мошенничество
        "field_5_7": "Нет",
        "msg_type": "08 Сообщение ЦОУ",
        "confidentiality": "не конфиденциально, не секретно",
        "cou_name": "ЦОУ г.Алматы",
        "cou_reg_number": "256310ac-c990-465c-bd2e-5a7b8e9e6c33",
        "cou_reg_date": "01.01.2026 03:01",
        "cou_position": "Финансовая организация",
        "cou_employee": "Антифрод центр",
        "city_phone": "",
        "mobile_phone": "77771015851",
        "email": "client@mail.ru"
    },
    # Кейс 2: Кража в Алматинском районе
    {
        "kui_number": "191200040000055",
        "reg_organ": "19120001",
        "district": "Алматинский район",
        "reg_date": "14.02.2026 10:15",
        "event_description": "Гр. Иванова заявила о краже кошелька в общественном транспорте маршрута №12. Ущерб 50 000 тенге.",
        "military_unit": "",
        "coupon_number": "AB-987654",
        "coupon_date": "14.02.2026",
        "field_5_1": "против собственности",
        "field_5_2": "",
        "field_5_3": "Нет",
        "field_5_4": "Нет",
        "field_5_5": "Нет",
        "field_5_6": "Нет",
        "field_5_7": "Нет",
        "msg_type": "08 Сообщение ЦОУ",
        "confidentiality": "не конфиденциально, не секретно",
        "cou_name": "ЦОУ г.Астана",
        "cou_reg_number": "AST-2026-0055",
        "cou_reg_date": "14.02.2026 09:45",
        "cou_position": "Оператор 102",
        "cou_employee": "Сержантов С.С.",
        "city_phone": "87172555555",
        "mobile_phone": "87011112233",
        "email": ""
    },
    # Кейс 3: ДП Жамбылской области (Воинская часть)
    {
        "kui_number": "314000050000099",
        "reg_organ": "31400001",
        "district": "ДП Жамбылской области",
        "reg_date": "20.03.2026 23:00",
        "event_description": "Попытка проникновения на территорию склада ГСМ неустановленными лицами.",
        "military_unit": "В/Ч 5513",
        "coupon_number": "VC-112233",
        "coupon_date": "20.03.2026",
        "field_5_1": "прочие",
        "field_5_2": "",
        "field_5_3": "Нет",
        "field_5_4": "Нет",
        "field_5_5": "Нет",
        "field_5_6": "Нет",
        "field_5_7": "Нет",
        "msg_type": "08 Сообщение ЦОУ",
        "confidentiality": "секретно",
        "cou_name": "ЦОУ Тараз",
        "cou_reg_number": "TRZ-998877",
        "cou_reg_date": "20.03.2026 22:50",
        "cou_position": "Дежурный офицер",
        "cou_employee": "Майоров М.М.",
        "city_phone": "",
        "mobile_phone": "87059998877",
        "email": "mil@gov.kz"
    }
]

def seed():
    print(f"Отправка данных на {URL}...")
    for i, case in enumerate(test_cases, 1):
        try:
            response = requests.post(URL, json=case)
            if response.status_code == 200:
                print(f"✅ Кейс {i} ({case['district']}) успешно загружен! ID: {response.json().get('id')}")
            else:
                print(f"❌ Ошибка в кейсе {i}: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            print("Убедитесь, что файл main.py запущен!")

if __name__ == "__main__":
    seed()