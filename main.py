# main.py
import os
import shutil
from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.staticfiles import StaticFiles

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


    # --- Вкладка 1: Дополнительные поля (которые раньше не работали) ---
    military_unit = Column(String, nullable=True)  # 3.1 Номер в/части
    coupon_number = Column(String, nullable=True)  # 4. Номер талона
    coupon_date = Column(String, nullable=True)  # 4. Дата талона

    # Нижние списки (5.1 - 5.7)
    field_5_1 = Column(String, nullable=True)  # Сообщение
    field_5_2 = Column(String, nullable=True)  # Зарегистрировано по рез.
    field_5_3 = Column(String, nullable=True)  # Связано с
    field_5_4 = Column(String, nullable=True)  # Предпринимательство
    field_5_5 = Column(String, nullable=True)  # Инвестиции
    field_5_6 = Column(String, nullable=True)  # Интернет-мошенничество
    field_5_7 = Column(String, nullable=True)  # Признак мошенничества
    audio_record = Column(String, nullable=True) # [НОВОЕ] 6. Запись аудио разговора

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


# --- Pydantic схема (Для загрузки через API) ---
class RegistrationSchema(BaseModel):
    # Вкладка 1
    kui_number: str = Field(..., example="263100030000001")
    reg_organ: str = Field(..., example="19310003")
    district: str = Field(..., example="Заводской район")
    reg_date: str = Field(..., example="13.01.2026 16:33")
    operator_conf_date: Optional[str] = Field(None, example="13.01.2026 17:00")
    event_description: str = Field(..., example="Банк остановил транзакцию...")

    # Новые поля для Вкладки 1
    military_unit: Optional[str] = Field(None, example="9999")
    coupon_number: Optional[str] = Field(None, example="AA-123456")
    coupon_date: Optional[str] = Field(None, example="13.01.2026")

    field_5_1: Optional[str] = Field(None, example="против собственности")
    field_5_2: Optional[str] = Field(None, example="")
    field_5_3: Optional[str] = Field(None, example="Нет")
    field_5_4: Optional[str] = Field(None, example="Нет")
    field_5_5: Optional[str] = Field(None, example="Нет")
    field_5_6: Optional[str] = Field(None, example="Да")
    field_5_7: Optional[str] = Field(None, example="Нет")
    audio_record: Optional[str] = Field(None, example="record_123.mp3") #Поле в схеме

    # Вкладка 2
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


@app.post("/api/external/receive_data")
def receive_data(data: RegistrationSchema, db: Session = Depends(get_db)):
    existing = db.query(Registration).filter(Registration.kui_number == data.kui_number).first()

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
        **latest.__dict__
    }


@app.get("/api/internal/get_latest")
def get_latest(db: Session = Depends(get_db)):
    latest = db.query(Registration).order_by(Registration.id.desc()).first()
    if not latest: return {"found": False}
    return {
        "found": True,
        **latest.__dict__
    }


# --- ДОБАВИТЬ ЭТОТ БЛОК ---
@app.get("/api/internal/search")
def search_by_kui(kui: str, db: Session = Depends(get_db)):
    # Ищем запись, где поле kui_number совпадает с переданным
    record = db.query(Registration).filter(Registration.kui_number == kui).first()

    if not record:
        return {"found": False}

    return {
        "found": True,
        **record.__dict__
    }


@app.post("/api/external/upload_audio")
def upload_audio_file(file: UploadFile = File(...)):
    # Сохраняем файл в папку static/audio
    file_location = f"static/audio/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    # Возвращаем имя файла, чтобы клиент мог сохранить его в JSON (в поле audio_record)
    return {"info": "File saved", "filename": file.filename, "url": f"/static/audio/{file.filename}"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)