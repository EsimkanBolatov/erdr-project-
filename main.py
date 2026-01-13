# main.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field  # <--- Добавили Field
from typing import Optional

# --- 1. Настройка Базы Данных (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./erdr_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 2. Модель БД (Таблица) ---
class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    kui_number = Column(String, unique=True, index=True)
    reg_organ = Column(String)
    district = Column(String)
    reg_date = Column(String)
    event_description = Column(Text)
    applicant_name = Column(String, nullable=True)
    applicant_phone = Column(String, nullable=True)
    applicant_city = Column(String, nullable=True)


# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)


# --- 3. Pydantic схема (С примерами для Swagger) ---
class RegistrationSchema(BaseModel):
    kui_number: str = Field(..., example="263100030000001", description="Уникальный номер КУИ")
    reg_organ: str = Field(..., example="19310003", description="Код органа")
    district: str = Field(..., example="Заводской район", description="Район события")
    reg_date: str = Field(..., example="13.01.2026 16:33", description="Дата и время")
    event_description: str = Field(
        ...,
        example="Банк остановил внутренний системой Антифрод данную транзакцию в связи с переводом подозреваемому дропперу. Клиент сомневается в совершении операции.",
        description="Фабула дела"
    )
    applicant_name: Optional[str] = Field(None, example="ЖАННАТ АЛЬХОДЖАЕВ МЕРЕЕВИЧ")
    applicant_phone: Optional[str] = Field(None, example="77771015851")
    applicant_city: Optional[str] = Field(None, example="Алматы")


# --- 4. Приложение FastAPI с описанием для Swagger ---
app = FastAPI(
    title="ERDR Simulator API",
    description="API для эмуляции работы ЕРДР и приема данных от внешних систем",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")


# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Роуты ---

@app.get("/", tags=["Фронтенд"])
def read_root(request: Request):
    """Открывает HTML страницу с формой (визуальный интерфейс)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/external/receive_data", tags=["Внешняя Интеграция"], summary="Принять данные (Имитация Антифрода)")
def receive_data(data: RegistrationSchema, db: Session = Depends(get_db)):
    """
    Этот метод принимает JSON данные (например, от банка или другой системы)
    и сохраняет их в базу данных SQLite.
    """
    # Проверяем, есть ли уже запись с таким КУИ
    existing = db.query(Registration).filter(Registration.kui_number == data.kui_number).first()

    if existing:
        # Обновляем существующую
        existing.event_description = data.event_description
        existing.applicant_name = data.applicant_name
        existing.applicant_phone = data.applicant_phone
        existing.applicant_city = data.applicant_city
        existing.reg_date = data.reg_date
        db.commit()
        return {"status": "updated", "message": f"Запись КУИ {data.kui_number} обновлена"}

    # Создаем новую
    new_reg = Registration(
        kui_number=data.kui_number,
        reg_organ=data.reg_organ,
        district=data.district,
        reg_date=data.reg_date,
        event_description=data.event_description,
        applicant_name=data.applicant_name,
        applicant_phone=data.applicant_phone,
        applicant_city=data.applicant_city
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return {"status": "created", "message": "Данные успешно записаны в БД", "id": new_reg.id}


@app.get("/api/internal/get_latest", tags=["Внутренний API"], summary="Получить последние данные для фронтенда")
def get_latest_data(db: Session = Depends(get_db)):
    """Отдает последнюю запись из базы для заполнения полей на сайте."""
    latest = db.query(Registration).order_by(Registration.id.desc()).first()
    if not latest:
        return {"found": False}
    return {
        "found": True,
        "kui_number": latest.kui_number,
        "reg_organ": latest.reg_organ,
        "district": latest.district,
        "reg_date": latest.reg_date,
        "event_description": latest.event_description,
        "applicant_name": latest.applicant_name,
        "applicant_phone": latest.applicant_phone,
        "applicant_city": latest.applicant_city
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)