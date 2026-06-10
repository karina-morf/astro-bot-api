from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

SYSTEM_PROMPT = """
Ти — сучасний, емпатичний та глибокий ШІ-астролог. 
Твоя мета — перетворювати точні астрологічні дані на зрозумілий текст.
"""

@app.post("/api/astrology")
async def generate_astrology_report(request: Request):
    """
    Цей ендпоінт приймає POST-запити з JSON-даними від Telegram-бота 
    або клієнта та повертає сформований промпт для ШІ.
    """
    try:
        # Отримуємо JSON від клієнта
        user_request = await request.json()
        
        report_type = user_request.get("report_type", "free")
        client_name = user_request.get("client_name", "Клієнт")
        astro_data = user_request.get("data", {})
        
        user_message = (
            f"Згенеруй звіт типу '{report_type}' для клієнта на ім'я {client_name}.\n"
            f"Ось астрологічні дані: {json.dumps(astro_data, ensure_ascii=False)}"
        )
        
        messages_for_api = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # Повертаємо успішну відповідь з нашими даними
        return JSONResponse(content={"status": "success", "messages": messages_for_api})

    except Exception as e:
        # У разі помилки повертаємо повідомлення про неї
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)