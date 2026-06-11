from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()

SYSTEM_PROMPT = """
Ти — сучасний, емпатичний та глибокий ШІ-астролог. 
Твоя мета — перетворювати точні астрологічні дані на зрозумілий текст.
Правила залежать від report_type:
- "free": тільки Сонце, Місяць, Асцендент. СТРОГО до 250 слів. Легка інтрига в кінці.
- "pro": детальний аналіз по блоках (Особистість, Кар'єра, Відносини, Таланти). До 800 слів.
- "subscription_daily": транзити та 1-2 конкретні поради. До 200 слів.
НІКОЛИ не вигадуй положення планет. Використовуй Markdown.
"""

@app.get("/")
async def root():
    return {"message": "Астро-бот API працює 🚀"}

@app.post("/api/astrology")
async def generate_astrology_report(request: Request):
    try:
        user_request = await request.json()
        
        report_type = user_request.get("report_type", "free")
        client_name = user_request.get("client_name", "Клієнт")
        
        # Якщо передані сирі дані (дата/час/місто) — розраховуємо карту
        if "birth_date" in user_request:
            birth_date = user_request.get("birth_date")  # ДД.ММ.РРРР
            birth_time = user_request.get("birth_time", "12:00")  # ГГ:ХХ
            birth_city = user_request.get("birth_city", "")
            birth_country = user_request.get("birth_country", "")

            # Отримуємо координати міста
            geolocator = Nominatim(user_agent="astro-bot")
            location = geolocator.geocode(f"{birth_city}, {birth_country}")
            
            if not location:
                return JSONResponse(content={"status": "error", "message": "Місто не знайдено"}, status_code=400)
            
            lat = location.latitude
            lon = location.longitude

            # Парсимо дату і час
            day, month, year = birth_date.split(".")
            hour, minute = birth_time.split(":")
            
            # Розраховуємо натальну карту
            date = Datetime(f"{year}/{month}/{day}", f"{hour}:{minute}", "+00:00")
            pos = GeoPos(lat, lon)
            chart = Chart(date, pos)

            sun = chart.get(const.SUN)
            moon = chart.get(const.MOON)
            asc = chart.get(const.ASC)
            mercury = chart.get(const.MERCURY)
            venus = chart.get(const.VENUS)
            mars = chart.get(const.MARS)
            jupiter = chart.get(const.JUPITER)
            saturn = chart.get(const.SATURN)

            astro_data = {
                "sun": {"sign": sun.sign, "house": sun.house},
                "moon": {"sign": moon.sign, "house": moon.house},
                "ascendant": {"sign": asc.sign},
                "mercury": {"sign": mercury.sign, "house": mercury.house},
                "venus": {"sign": venus.sign, "house": venus.house},
                "mars": {"sign": mars.sign, "house": mars.house},
                "jupiter": {"sign": jupiter.sign, "house": jupiter.house},
                "saturn": {"sign": saturn.sign, "house": saturn.house},
            }
        else:
            # Якщо передані готові дані напряму
            astro_data = user_request.get("data", {})

        user_message = (
            f"Згенеруй звіт типу '{report_type}' для клієнта на ім'я {client_name}.\n"
            f"Ось астрологічні дані: {json.dumps(astro_data, ensure_ascii=False)}"
        )

        messages_for_api = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        return JSONResponse(content={"status": "success", "messages": messages_for_api})

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)
