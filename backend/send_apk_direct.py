import asyncio
import httpx
import os

async def main():
    token = '8640045696:AAGf_2-5YffGjht4jTQTKGWb3ltSf4uWcY8'
    chat_id = '1801746044'
    url = f'https://api.telegram.org/bot{token}/sendDocument'
    apk_path = r'd:\BurgoodAccsesCantrol\apk\BurgoodAccessControl.apk'
    
    caption = (
        "🦅 <b>Burgood Access Control - Yangilangan APK (v1.0.3)</b>\n\n"
        "✨ <b>Siz aytgan barcha kamchiliklar bartaraf etildi:</b>\n\n"
        "1. 🚫 <b>Xalaqit berayotgan Sozlamalar (⚙️) tugmasi butunlay olib tashlandi!</b>\n"
        "• Endi Menyu (<code>☰</code>) tugmasi ustiga hech qanday belgi tushmaydi, bemalol bosiladi.\n\n"
        "2. 📱 <b>Header va Telefon Status Bar (Soat/Batareya) to'qnashuvi tuzatildi:</b>\n"
        "• Telefoningizning soati, batareya va Wi-Fi belgilari ilova headeri (logo va nom) ustiga tushib qolmaydi — tepadan xavfsiz oraliq (safe insets) berildi.\n\n"
        "3. 💎 <b>Header dizayni chiroyli va tartibli qilindi:</b>\n"
        "• Rasmiy Burgood logotipi alohida ramkada, korxona/universitet nomi va <b>ACCESS CONTROL</b> yozuvi aniq ko'rinadi.\n\n"
        "📲 <b>O'RNATISH TARTIBI:</b>\n"
        "1. Telefoningizdagi eski ilovani o'chirib tashlang (Удалить).\n"
        "2. Ushbu yangi APK faylini yuklab oling va bosing.\n"
        "3. 'O'rnatish' (Установить) ni bosing va ilovaga kiring!"
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(apk_path, 'rb') as f:
            files = {'document': ('BurgoodAccessControl.apk', f, 'application/vnd.android.package-archive')}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            res = await client.post(url, data=data, files=files)
            print("Status Code:", res.status_code, "OK:", res.json().get('ok', False))

if __name__ == "__main__":
    asyncio.run(main())
