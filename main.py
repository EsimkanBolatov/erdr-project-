# main.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import Optional

# --- Настройка БД ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./erdr_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Модель БД ---
class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    # Вкладка 1
    kui_number = Column(String, unique=True, index=True)
    reg_organ = Column(String)
    district = Column(String)
    reg_date = Column(String)
    event_description = Column(Text)

    # Вкладка 2 (Новые поля по скриншоту)
    msg_type = Column(String, nullable=True)  # 20. Вид сообщения
    confidentiality = Column(String, nullable=True)  # 20.1 Сведения
    cou_name = Column(String, nullable=True)  # 22. Название ЦОУ
    cou_reg_number = Column(String, nullable=True)  # 22.1 Номер регистрации в ЦОУ
    cou_reg_date = Column(String, nullable=True)  # 22.1 Дата-время в ЦОУ
    cou_position = Column(String, nullable=True)  # 22.2 Должность
    cou_employee = Column(String, nullable=True)  # 22.3 Фамилия сотрудника

    city_phone = Column(String, nullable=True)  # 25. Город тел
    mobile_phone = Column(String, nullable=True)  # 25. Моб тел
    email = Column(String, nullable=True)  # 25. e-mail

    # Старые поля (оставим для совместимости, если нужны)
    applicant_name = Column(String, nullable=True)
    applicant_phone = Column(String, nullable=True)
    applicant_city = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


# --- Pydantic схема (Данные со скриншота для теста) ---
class RegistrationSchema(BaseModel):
    # Вкладка 1
    kui_number: str = Field(..., example="263100030000001")
    reg_organ: str = Field(..., example="19310003")
    district: str = Field(..., example="Заводской район")
    reg_date: str = Field(..., example="13.01.2026 16:33")
    event_description: str = Field(..., example="Банк остановил транзакцию...")

    # Вкладка 2 (Точь-в-точь как на фото)
    msg_type: str = Field(..., example="08 Сообщение ЦОУ")
    confidentiality: str = Field(..., example="не конфиденциально, не секретно")
    cou_name: str = Field(..., example="ЦОУ г.Алматы")
    cou_reg_number: str = Field(..., example="256310ac-c990-465c-bd2e-5a7b8e9e6c33")
    cou_reg_date: str = Field(..., example="01.01.2026 03:01")
    cou_position: str = Field(..., example="Финансовая организация")
    cou_employee: str = Field(..., example="Антифрод центр")
    city_phone: Optional[str] = Field(None, example="")
    mobile_phone: Optional[str] = Field(..., example="77771015851")
    email: Optional[str] = Field(None, example="")


app = FastAPI(title="ERDR Simulator")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/external/receive_data")
def receive_data(data: RegistrationSchema, db: Session = Depends(get_db)):
    existing = db.query(Registration).filter(Registration.kui_number == data.kui_number).first()

    # Если запись есть, удалим старую для теста (чтобы обновить все поля)
    if existing:
        db.delete(existing)
        db.commit()

    new_reg = Registration(**data.dict())
    db.add(new_reg)
    db.commit()
    return {"status": "ok", "id": new_reg.id}


@app.get("/api/internal/get_latest")
def get_latest(db: Session = Depends(get_db)):
    latest = db.query(Registration).order_by(Registration.id.desc()).first()
    if not latest: return {"found": False}
    return {
        "found": True,
        **latest.__dict__  # Распаковываем все поля
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)