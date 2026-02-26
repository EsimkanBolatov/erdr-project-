# main.py
import os
import shutil
import requests  # НОВОЕ: Для HTTP-запросов к стороннему API
from dotenv import load_dotenv  # НОВОЕ: Для загрузки переменных из .env локально
from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel, Field
from typing import Optional

# --- НОВОЕ: Загрузка переменных окружения ---
# Читаем файл .env (если он есть локально) до инициализации приложения
load_dotenv()

# Достаем ссылку на сторонний API. Если её нет, переменная будет None
EXTERNAL_API_URL = os.getenv("THIRD_PARTY_API_URL")


# --- Настройка БД ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./erdr_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Модель БД ---
class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)

    # --- Вкладка 1: Основные поля ---
    kui_number = Column(String, unique=True, index=True)
    reg_organ = Column(String)
    district = Column(String)
    reg_date = Column(String)
    operator_conf_date = Column(String, nullable=True)
    event_description = Column(Text)

    # --- Вкладка 1: Дополнительные поля ---
    military_unit = Column(String, nullable=True)  
    coupon_number = Column(String, nullable=True)  
    coupon_date = Column(String, nullable=True)    

    field_5_1 = Column(String, nullable=True)  
    field_5_2 = Column(String, nullable=True)  
    field_5_3 = Column(String, nullable=True)  
    field_5_4 = Column(String, nullable=True)  
    field_5_5 = Column(String, nullable=True)  
    field_5_6 = Column(String, nullable=True)  
    field_5_7 = Column(String, nullable=True)  
    
    # [ОБНОВЛЕНИЕ] Разделенные аудиофайлы
    audio_caller = Column(String, nullable=True) 
    audio_operator = Column(String, nullable=True)

    # --- Вкладка 2: Данные заявителя/ЦОУ ---
    msg_type = Column(String, nullable=True)
    confidentiality = Column(String, nullable=True)
    cou_name = Column(String, nullable=True)
    cou_reg_number = Column(String, nullable=True)
    cou_reg_date = Column(String, nullable=True)
    cou_position = Column(String, nullable=True)
    cou_employee = Column(String, nullable=True)

    city_phone = Column(String, nullable=True)
    mobile_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


# --- Pydantic схема ---
class RegistrationSchema(BaseModel):
    kui_number: str = Field(..., json_schema_extra={"example": "263100030000001"})
    reg_organ: str = Field(..., json_schema_extra={"example": "19310003"})
    district: str = Field(..., json_schema_extra={"example": "Заводской район"})
    reg_date: str = Field(..., json_schema_extra={"example": "13.01.2026 16:33"})
    operator_conf_date: Optional[str] = Field(None, json_schema_extra={"example": "13.01.2026 17:00"})
    event_description: str = Field(..., json_schema_extra={"example": "Банк остановил транзакцию..."})

    military_unit: Optional[str] = Field(None)
    coupon_number: Optional[str] = Field(None)
    coupon_date: Optional[str] = Field(None)

    field_5_1: Optional[str] = Field(None)
    field_5_2: Optional[str] = Field(None)
    field_5_3: Optional[str] = Field(None)
    field_5_4: Optional[str] = Field(None)
    field_5_5: Optional[str] = Field(None)
    field_5_6: Optional[str] = Field(None)
    field_5_7: Optional[str] = Field(None)
    
    # [ОБНОВЛЕНИЕ]
    audio_caller: Optional[str] = Field(None, json_schema_extra={"example": "record_caller.wav"}) 
    audio_operator: Optional[str] = Field(None, json_schema_extra={"example": "record_ai.wav"})

    msg_type: str = Field(..., json_schema_extra={"example": "08 Сообщение ЦОУ"})
    confidentiality: str = Field(..., json_schema_extra={"example": "не конфиденциально"})
    cou_name: str = Field(..., json_schema_extra={"example": "ЦОУ г.Алматы"})
    cou_reg_number: str = Field(..., json_schema_extra={"example": "256310ac-c990-465c"})
    cou_reg_date: str = Field(..., json_schema_extra={"example": "01.01.2026 03:01"})
    cou_position: str = Field(..., json_schema_extra={"example": "Финансовая организация"})
    cou_employee: str = Field(..., json_schema_extra={"example": "Антифрод центр"})
    city_phone: Optional[str] = Field(None)
    mobile_phone: Optional[str] = Field(..., json_schema_extra={"example": "77771015851"})
    email: Optional[str] = Field(None)


app = FastAPI(title="ERDR Simulator")

# НАСТРОЙКА CORS ДЛЯ СЕРВЕРА
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # На проде лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- НОВОЕ: Эндпоинт для запроса к стороннему API ---
@app.get("/api/internal/fetch_from_third_party")
def fetch_external_data():
    """Получает данные из сторонней системы через API"""
    if not EXTERNAL_API_URL:
        # Если забыли добавить .env локально или Environment Variable на Render
        raise HTTPException(
            status_code=500, 
            detail="Внутренняя ошибка: THIRD_PARTY_API_URL не настроен."
        )
    
    try:
        # Делаем GET запрос к внешнему API
        response = requests.get(EXTERNAL_API_URL, timeout=10)
        
        # Если вернулась ошибка 4xx или 5xx, перехватываем её
        response.raise_for_status() 
        
        # Возвращаем JSON, полученный от стороннего сайта
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к внешнему API: {e}")
        raise HTTPException(status_code=502, detail="Не удалось получить данные от стороннего сервиса")
# ---------------------------------------------------

@app.post("/api/external/receive_data")
def receive_data(data: RegistrationSchema, db: Session = Depends(get_db)):
    existing = db.query(Registration).filter(Registration.kui_number == data.kui_number).first()

    if existing:
        db.delete(existing)
        db.commit()

    new_reg = Registration(**data.model_dump()) 
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return {"status": "ok", "id": new_reg.id}

@app.get("/api/internal/get_latest")
def get_latest(db: Session = Depends(get_db)):
    latest = db.query(Registration).order_by(Registration.id.desc()).first()
    if not latest: return {"found": False}
    return {
        "found": True,
        **latest.__dict__
    }

@app.get("/api/internal/search")
def search_by_kui(kui: str, db: Session = Depends(get_db)):
    record = db.query(Registration).filter(Registration.kui_number == kui).first()
    if not record:
        return {"found": False}
    return {
        "found": True,
        **record.__dict__
    }

@app.post("/api/external/upload_audio")
def upload_audio_file(file: UploadFile = File(...)):
    file_location = f"static/audio/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return {"info": "File saved", "filename": file.filename, "url": f"/static/audio/{file.filename}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)