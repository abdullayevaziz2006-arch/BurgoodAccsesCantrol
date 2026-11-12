import asyncio
import httpx
import random
from datetime import datetime

"""
Bu skript tarmoqda real Hikvision qurilmasi bo'lmagan holda yoki
sinov maqsadida virtual o'tish hodisalarini (Face Match) simulyatsiya qilish uchun.
U to'g'ridan-to'g'ri backendning event workerini sinash uchun bazaga log yozadi yoki WebSocketni tekshiradi.
"""

from app.core.database import SessionLocal
from app.models.models import Device, User, AccessLog, DirectionType, DeviceStatus
from app.services.websocket import ws_manager

async def seed_demo_data():
    db = SessionLocal()
    
    # 1. Demo Device (Turniket) yaratish
    demo_device = db.query(Device).filter(Device.ip_address == "192.168.1.120").first()
    if not demo_device:
        demo_device = Device(
            name="Turniket 1 (Bosh bino - Kirish)",
            ip_address="192.168.1.120",
            port=80,
            username="admin",
            password="Password123!",
            direction=DirectionType.ENTRY,
            location="Bosh bino 1-qavat",
            status=DeviceStatus.ONLINE,
            model="DS-K1T671MF",
            serial_number="DS-K1T671MF20230915V030200",
            firmware_version="V3.2.0 build 230915",
            last_seen=datetime.utcnow()
        )
        db.add(demo_device)
        db.commit()
        db.refresh(demo_device)
        print("Demo Device yaratildi:", demo_device.name)

    demo_device_exit = db.query(Device).filter(Device.ip_address == "192.168.1.121").first()
    if not demo_device_exit:
        demo_device_exit = Device(
            name="Turniket 2 (Bosh bino - Chiqish)",
            ip_address="192.168.1.121",
            port=80,
            username="admin",
            password="Password123!",
            direction=DirectionType.EXIT,
            location="Bosh bino 1-qavat",
            status=DeviceStatus.ONLINE,
            model="DS-K1T671MF",
            serial_number="DS-K1T671MF20230916V030201",
            firmware_version="V3.2.0 build 230915",
            last_seen=datetime.utcnow()
        )
        db.add(demo_device_exit)
        db.commit()
        print("Demo Exit Device yaratildi:", demo_device_exit.name)

    # 2. Demo Talaba va O'qituvchilar yaratish
    demo_users = [
        {"emp": "391001", "name": "Akmal Jo'rayev", "role": "student", "group": "941-21"},
        {"emp": "391002", "name": "Madina Karimova", "role": "student", "group": "942-21"},
        {"emp": "391003", "name": "Prof. Sherzod Rahimov", "role": "teacher", "group": "Kafedra mudiri"},
        {"emp": "391004", "name": "Jasur Boboyev", "role": "student", "group": "941-21"},
    ]

    for u in demo_users:
        existing = db.query(User).filter(User.employee_no == u["emp"]).first()
        if not existing:
            new_u = User(
                employee_no=u["emp"],
                full_name=u["name"],
                role=u["role"],
                group_name=u["group"]
            )
            db.add(new_u)
    db.commit()
    print("Demo Foydalanuvchilar yaratildi.")

    db.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
