# Universitet Turniket & Face ID CRM Tizimi

Hikvision Face ID terminallari (ISAPI protokoli orqali) bilan integratsiya qilingan universitet kirish-chiqish nazorati va talabalar/xodimlar davomatini boshqaruvchi to'liq CRM platformasi.

---

## 🚀 Texnologiyalar Steki

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (SQLite / PostgreSQL), HTTPX Digest Authentication, WebSockets, OpenPyXL (Excel eksport).
- **Frontend**: React 18, TypeScript, Tailwind CSS v4, Lucide Icons, Axios, Vite.
- **Qurilmalar bilan integratsiya**: Hikvision ISAPI (Intelligent Security API) HTTP Digest Auth orqali:
  - Uzluksiz voqealar oqimi: `GET /ISAPI/Event/notification/alertStream`
  - Foydalanuvchilar ma'lumotlari: `PUT /ISAPI/AccessControl/UserInfo/Record`
  - Yuz rasmlarini yuklash: `POST /ISAPI/Intelligent/FDLib/FaceDataRecord` (Multipart form-data)
  - Turniket eshigini masofadan ochish: `PUT /ISAPI/AccessControl/RemoteControl/door/1`

---

## 🛠 Ishga tushirish (Qadam-baqadam)

### 1. Backendni ishga tushirish (FastAPI)

Terminalda (PowerShell yoki CMD):
```powershell
cd d:\BurgoodAccsesCantrol\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Hujjatlari (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- WebSocket Jonli Oqim: `ws://localhost:8000/ws/live-events`

### 2. Frontendni ishga tushirish (React)

Yangi terminal oynasida:
```powershell
cd d:\BurgoodAccsesCantrol\frontend
npm run dev
```

- CRM Boshqaruv Paneli: [http://localhost:3000](http://localhost:3000)

---

## 🌟 Asosiy Imkoniyatlar

1. **Terminallar (Face ID Turniketlar) Boshqaruvi**:
   - Terminalning IP manzili, porti, admin logini va parolini kiritish orqali tezkor ulash.
   - **ISAPI Sinov (Test Connection)**: Terminal modeli, seriya raqami va proshivkasini ISAPI orqali avtomatik aniqlash.
   - **Masofadan Eshikni Ochish (Remote Door Open)**: Favqulodda holatlar yoki operator uchun bir klik bilan turniketni ochish.
2. **Talabalar va Xodimlar**:
   - Talaba / Xodim shaxsiy ma'lumotlari va rollari (Talaba, O'qituvchi, Xodim).
   - Yuz rasmini (Face Picture) yuklash.
   - **"Turniketlarga Yuborish"**: Foydalanuvchi ma'lumotlari va uning yuz fotosuratini tarmoqdagi barcha yoki tanlangan Hikvision Face ID terminallariga ISAPI protokoli orqali avtomatik sinxronizatsiya qilish.
3. **Jonli Real-time Monitoring**:
   - WebSocket orqali millisekundlarda yangilanib turadigan o'tishlar oqimi.
   - Kim kirgani/chiqqani (talaba surati, ismi, guruhi, turniket nomi va vaqti) darhol ekranda aks etadi.
4. **Davomat va Hisobotlar**:
   - Kunlik, oylik kirish-chiqishlar statistikasi.
   - Excel (`.xlsx`) formatida davomat hisobotlarini bitta tugma orqali yuklab olish.
