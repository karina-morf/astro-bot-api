from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from geopy.geocoders import Nominatim
import swisseph as swe
from datetime import datetime

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

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def get_sign(degree):
    return SIGNS[int(degree / 30)]

def get_house_number(degree, houses):
    for i in range(12):
        start = houses[i]
        end = houses[(i + 1) % 12]
        if start <= end:
            if start <= degree < end:
                return i + 1
        else:
            if degree >= start or degree < end:
                return i + 1
    return 1

def calculate_chart(birth_date, birth_time, lat, lon):
    day, month, year = birth_date.split(".")
    hour, minute = birth_time.split(":")
    
    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
    
    houses_data, ascmc = swe.houses(jd, lat, lon, b'P')
    asc_degree = ascmc[0]
    
    planets = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
        "jupiter": swe.JUPITER,
        "saturn": swe.SATURN,
    }
    
    result = {"ascendant": {"sign": get_sign(asc_degree)}}
    
    for name, planet_id in planets.items():
        pos, _ = swe.calc_ut(jd, planet_id)
        degree = pos[0]
        result[name] = {
            "sign": get_sign(degree),
            "house": get_house_number(degree, list(houses_data))
        }
    
    return result

@app.get("/")
async def root():
    return {"message": "Астро-бот API працює 🚀"}

@app.post("/api/astrology")
async def generate_astrology_report(request: Request):
    try:
        user_request = await request.json()
        
        report_type = user_request.get("report_type", "free")
        client_name = user_request.get("client_name", "Клієнт")
        
        if "birth_date" in user_request:
            birth_date = user_request.get("birth_date")
            birth_time = user_request.get("birth_time", "12:00")
            birth_city = user_request.get("birth_city", "")
            birth_country = user_request.get("birth_country", "")

            geolocator = Nominatim(user_agent="astro-bot")
            location = geolocator.geocode(f"{birth_city}, {birth_country}")
            
            if not location:
                return JSONResponse(content={"status": "error", "message": "Місто не знайдено"}, status_code=400)
            
            astro_data = calculate_chart(birth_date, birth_time, location.latitude, location.longitude)
        else:
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
