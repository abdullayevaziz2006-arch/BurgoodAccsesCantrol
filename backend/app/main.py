from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import Base, engine
from app.api import devices, users, attendance, structure, schedules, auth, master
from app.services.websocket import ws_manager
from app.services.event_streamer import event_stream_worker
from app.services.telegram_bot import telegram_bot
from app.services.telegram_master_bot import telegram_master_bot
from fastapi.responses import FileResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ma'lumotlar bazasi jadvallarini yaratish
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ilova ishga tushganda alertStream workerini boshlash
    logger.info("Hikvision Event Stream Worker boshlanmoqda...")
    await event_stream_worker.start()
    
    # Telegram Bot Polling (agar sozlamalarda yoqilgan bo'lsa)
    if settings.ENABLE_TELEGRAM_BOT:
        logger.info("Telegram Client Bot boshlanmoqda...")
        await telegram_bot.start()

        logger.info("Telegram Master Bot boshlanmoqda...")
        await telegram_master_bot.start()
    else:
        logger.info("Telegram botlar lokal rejimda o'chirilgan (ENABLE_TELEGRAM_BOT=False).")
    
    yield
    
    # To'xtaganda tozalash
    if settings.ENABLE_TELEGRAM_BOT:
        logger.info("Telegram Master Bot to'xtatilmoqda...")
        await telegram_master_bot.stop()

        logger.info("Telegram Client Bot to'xtatilmoqda...")
        await telegram_bot.stop()
    
    logger.info("Hikvision Event Stream Worker to'xtatilmoqda...")
    await event_stream_worker.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS sozlamasi (Frontenddan so'rovlar uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads papkasini statik fayl sifatida ulash
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR, follow_symlink=True), name="uploads")

# REST API Routerlar
app.include_router(devices.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(attendance.router, prefix=settings.API_V1_STR)
app.include_router(structure.router, prefix=settings.API_V1_STR)
app.include_router(schedules.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(master.router, prefix=settings.API_V1_STR)

# Telegram Mini App (Web App) HTML sahifasi
MINIAPP_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "miniapp.html")
PRIVACY_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "privacy.html")

@app.get("/miniapp")
def get_miniapp():
    if os.path.exists(MINIAPP_HTML):
        response = FileResponse(MINIAPP_HTML)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return {"status": "error", "message": "Mini App fayli topilmadi"}

@app.get("/privacy")
@app.get("/privacy-policy")
def get_privacy_policy():
    if os.path.exists(PRIVACY_HTML):
        return FileResponse(PRIVACY_HTML)
    return {"status": "error", "message": "Privacy Policy sahifasi topilmadi"}

# Hikvision HTTP Listening (Terminal Events)
from app.services.hikvision_listener import handle_hikvision_http_event
from app.core.database import get_db
from fastapi import Request, Depends

@app.post("/api/v1/terminal-events")
@app.post("/api/v1/terminal-events/")
async def terminal_events_listener(request: Request, db = Depends(get_db)):
    return await handle_hikvision_http_event(request, db)

@app.get("/download-apk")
@app.get("/uploads/BurgoodAccessControl.apk")
def download_apk_file():
    apk_paths = [
        os.path.join(settings.UPLOAD_DIR, "BurgoodAccessControl.apk"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apk", "BurgoodAccessControl.apk"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BurgoodAccessControl.apk"),
    ]
    for p in apk_paths:
        if os.path.exists(p):
            return FileResponse(
                path=p,
                media_type="application/vnd.android.package-archive",
                filename="BurgoodAccessControl.apk",
                headers={
                    "Content-Disposition": 'attachment; filename="BurgoodAccessControl.apk"',
                    "Content-Type": "application/vnd.android.package-archive"
                }
            )
    return {"status": "error", "message": "APK fayli topilmadi"}

# Real-time WebSocket Endpoint
@app.websocket("/ws/live-events")
async def websocket_live_events(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mijozdan yurak urishi (ping) qabul qilish
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket xatosi: {e}")
        ws_manager.disconnect(websocket)

# Agar frontend/dist mavjud bo'lsa - to'g'ridan-to'g'ri dastur sifatida ulash (Node.js siz ishlash uchun)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend_dist")
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": settings.PROJECT_NAME,
            "docs": "/docs"
        }
