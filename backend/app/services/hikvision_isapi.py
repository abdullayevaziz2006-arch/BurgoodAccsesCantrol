import httpx
import xml.etree.ElementTree as ET
import json
import logging
from typing import Optional, Dict, Any, Tuple
import os
import re

logger = logging.getLogger(__name__)

def format_isapi_error(resp_text: str, status_code: int) -> str:
    """ISAPI xatoliklarini foydalanuvchiga tushunarli o'zbek tiliga o'girish"""
    if "lockStatus" in resp_text and "lock" in resp_text:
        m = re.search(r'<unlockTime>(\d+)</unlockTime>', resp_text)
        mins = f"{int(m.group(1)) // 60} daqiqa" if m else "30 daqiqa"
        return f"Terminal xavfsizlik himoyasi sababli bloklangan (Lock). Blokdan chiqarish uchun terminalni o'chirib qayta yoqing (tokdan uzib yoqing) yoki {mins} kuting."
    if status_code == 401:
        return "Terminal paroli yoki foydalanuvchi nomi noto'g'ri (401 Unauthorized)"
    if "deviceUserAlreadyExistFace" in resp_text:
        return "Yuz rasmi terminalda allaqachon mavjud"
    return f"Xatolik: {status_code} - {resp_text[:120]}"

class HikvisionISAPI:
    """
    Hikvision Face ID / Turniket terminallari uchun ISAPI drayveri.
    HTTP Digest Authentication orqali ulanadi.
    """
    def __init__(self, ip: str, port: int = 80, username: str = "admin", password: str = ""):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{self.ip}:{self.port}"
        self.auth = httpx.DigestAuth(username=self.username, password=self.password)

    async def get_device_info(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Terminal ma'lumotlarini olish (Device Model, Serial Number, Firmware).
        GET /ISAPI/System/deviceInfo
        """
        url = f"{self.base_url}/ISAPI/System/deviceInfo"
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=4.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    # XML javobini tahlil qilish
                    root = ET.fromstring(resp.text)
                    # Namespace tozalash
                    ns = {"ns": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
                    
                    def find_val(tag_name):
                        el = root.find(f".//{tag_name}")
                        if el is None and ns:
                            el = root.find(f".//{{{ns['ns']}}}{tag_name}")
                        return el.text if el is not None else None

                    data = {
                        "deviceName": find_val("deviceName") or "Hikvision Terminal",
                        "deviceID": find_val("deviceID"),
                        "model": find_val("model") or "Face Terminal",
                        "serialNumber": find_val("serialNumber") or "",
                        "firmwareVersion": find_val("firmwareVersion") or "",
                        "firmwareReleasedDate": find_val("firmwareReleasedDate") or "",
                    }
                    return True, data
                else:
                    return False, {"error": f"Status: {resp.status_code}", "detail": resp.text}
        except Exception as e:
            logger.error(f"Error fetching deviceInfo from {self.ip}: {e}")
            return False, {"error": str(e)}

    async def set_custom_prompt(self, success_text: str = "Xush kelibsiz") -> Tuple[bool, str]:
        """
        Terminal yuzni taniganda ekranda yoki ovozda chiqadigan xabarni sozlash
        PUT /ISAPI/AccessControl/CustomPrompt?format=json
        """
        url = f"{self.base_url}/ISAPI/AccessControl/CustomPrompt?format=json"
        payload = {
            "enabled": True,
            "PromptList": [
                {"promptType": "authenticationSuccess", "promptContent": success_text[:16]}
            ]
        }
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                resp = await client.put(url, json=payload, headers=headers)
                if resp.status_code in [200, 201]:
                    return True, "Maxsus xabar sozlandi"
                return False, f"Xatolik: {resp.status_code}"
        except Exception as e:
            return False, str(e)

    async def configure_attendance_status_keys(self, options: list) -> Tuple[bool, str]:
        """
        Face ID terminal ekraniga tanlangan holatlarni (Kirish, Chiqish, Tushlik) yozish va faollashtirish.
        """
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                
                # 1. Rejimni manualAndAuto yoki manual qilish
                mode_url = f"{self.base_url}/ISAPI/AccessControl/Configuration/attendanceMode?format=json"
                mode_payload = {
                    "AttendanceMode": {
                        "mode": "manualAndAuto",
                        "attendanceStatusTime": 20,
                        "reqAttendanceStatus": True
                    }
                }
                await client.put(mode_url, json=mode_payload, headers=headers)

                # 2. 4 ta holat tugmalarini sozlash
                keys_mapping = [
                    (1, "check_in" in options, "checkIn", "Kirish"),
                    (2, "check_out" in options, "checkOut", "Chiqish"),
                    (3, "break_out" in options, "breakOut", "Tushlik chiqish"),
                    (4, "break_in" in options, "breakIn", "Tushlik kirish"),
                    (5, False, "overtimeIn", "Overtime In"),
                    (6, False, "overtimeOut", "Overtime Out")
                ]
                for kid, en, st, lb in keys_mapping:
                    key_url = f"{self.base_url}/ISAPI/AccessControl/keyCfg/{kid}/attendance?format=json"
                    key_payload = {
                        "Attendance": {
                            "enable": en,
                            "attendanceStatus": st,
                            "label": lb
                        }
                    }
                    await client.put(key_url, json=key_payload, headers=headers)

                return True, "Terminal ekrani holatlari muvaffaqiyatli sozlandi"
        except Exception as e:
            logger.error(f"Error configuring attendance keys on {self.ip}: {e}")
            return False, str(e)

    async def remote_door_control(self, door_no: int = 1, cmd: str = "open") -> Tuple[bool, str]:
        """
        Turniket eshigini masofadan ochish yoki yopish.
        PUT /ISAPI/AccessControl/RemoteControl/door/<door_no>
        cmd: 'open', 'close', 'alwaysOpen', 'alwaysClose'
        """
        url = f"{self.base_url}/ISAPI/AccessControl/RemoteControl/door/{door_no}"
        xml_body = f"""<RemoteControlDoor xmlns="http://www.isapi.org/ver20/XMLSchema" version="2.0">
    <cmd>{cmd}</cmd>
</RemoteControlDoor>"""
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
                headers = {"Content-Type": "application/xml"}
                resp = await client.put(url, content=xml_body, headers=headers)
                if resp.status_code in [200, 204]:
                    return True, "Buyruq muvaffaqiyatli bajarildi"
                return False, f"Xatolik: {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Ulanishda xatolik: {str(e)}"

    async def set_user_info(self, employee_no: str, name: str, user_type: str = "normal") -> Tuple[bool, str]:
        """
        Foydalanuvchini (xodim/talaba) terminalga qo'shish yoki yangilash.
        Hikvision ISAPI da SetUp yoki Modify ishlatiladi:
        PUT /ISAPI/AccessControl/UserInfo/SetUp?format=json
        """
        payload = {
            "UserInfo": {
                "employeeNo": str(employee_no),
                "name": name,
                "userType": user_type,
                "closeDelay": 5,
                "Valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2035-12-31T23:59:59",
                    "timeType": "local"
                },
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ]
            }
        }
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                
                # 1. SetUp - yangi yoki mavjud foydalanuvchini sozlash/qo'shish (eng universal endpoint)
                url_setup = f"{self.base_url}/ISAPI/AccessControl/UserInfo/SetUp?format=json"
                resp = await client.put(url_setup, json=payload, headers=headers)
                if resp.status_code in [200, 201]:
                    return True, "Foydalanuvchi muvaffaqiyatli saqlandi"

                # 2. Modify - agar foydalanuvchi allaqachon mavjud bo'lsa
                url_mod = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Modify?format=json"
                resp_mod = await client.put(url_mod, json=payload, headers=headers)
                if resp_mod.status_code in [200, 201]:
                    return True, "Foydalanuvchi muvaffaqiyatli yangilandi"

                # 3. Record - ba'zi eski proshivkalar uchun
                url_rec = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Record?format=json"
                resp_rec = await client.put(url_rec, json=payload, headers=headers)
                if resp_rec.status_code in [200, 201]:
                    return True, "Foydalanuvchi muvaffaqiyatli saqlandi"

                resp_post = await client.post(url_rec, json=payload, headers=headers)
                if resp_post.status_code in [200, 201]:
                    return True, "Foydalanuvchi muvaffaqiyatli saqlandi"

                return False, format_isapi_error(resp.text, resp.status_code)
        except Exception as e:
            return False, f"Ulanishda xatolik: {str(e)}"

    async def delete_user(self, employee_no: str) -> Tuple[bool, str]:
        """
        Foydalanuvchini terminaldan o'chirish.
        PUT /ISAPI/AccessControl/UserInfoDetail/Delete?format=json
        """
        url = f"{self.base_url}/ISAPI/AccessControl/UserInfoDetail/Delete?format=json"
        payload = {
            "UserInfoDetail": {
                "mode": "byEmployeeNo",
                "EmployeeNoList": [
                    {"employeeNo": str(employee_no)}
                ]
            }
        }
        try:
            # Yuz rasmini ham tozalab qo'yamiz
            await self.delete_face(employee_no)
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                resp = await client.put(url, json=payload, headers=headers)
                if resp.status_code in [200, 204]:
                    return True, "Foydalanuvchi terminaldan o'chirildi"
                
                # Agar UserInfoDetail mos kelmasa UserInfo/Delete ni sinaymiz
                url_alt = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Delete?format=json"
                payload_alt = {
                    "UserInfoDelCond": {
                        "EmployeeNoList": [{"employeeNo": str(employee_no)}]
                    }
                }
                resp_alt = await client.put(url_alt, json=payload_alt, headers=headers)
                if resp_alt.status_code in [200, 204]:
                    return True, "Foydalanuvchi terminaldan o'chirildi"

                return False, format_isapi_error(resp.text, resp.status_code)
        except Exception as e:
            return False, f"Ulanishda xatolik: {str(e)}"

    async def delete_face(self, employee_no: str) -> Tuple[bool, str]:
        """Eski yuz rasmini terminaldan o'chirish"""
        url_fdlib = f"{self.base_url}/ISAPI/Intelligent/FDLib/FaceDataRecord/Delete?format=json"
        payload_fdlib = {
            "FaceDataRecordDelete": {
                "mode": "byFPID",
                "FPIDList": [{"value": str(employee_no)}]
            }
        }
        url_ac = f"{self.base_url}/ISAPI/AccessControl/FaceRecord/Delete?format=json"
        payload_ac = {
            "FaceRecordDelete": {
                "mode": "byEmployeeNo",
                "EmployeeNoList": [{"employeeNo": str(employee_no)}]
            }
        }
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=5.0) as client:
                r1 = await client.put(url_fdlib, json=payload_fdlib)
                if r1.status_code in [200, 204]:
                    return True, "Eski rasm o'chirildi"
                r2 = await client.put(url_ac, json=payload_ac)
                if r2.status_code in [200, 204]:
                    return True, "Eski rasm o'chirildi"
        except Exception:
            pass
        return False, "O'chirilmadi"

    async def upload_face_picture(self, employee_no: str, image_bytes: bytes) -> Tuple[bool, str]:
        """
        Foydalanuvchining yuz rasmini terminalga yuklash.
        Hikvision ISAPI FDLib yoki FaceRecord multipart/form-data orqali qabul qiladi.
        POST /ISAPI/Intelligent/FDLib/FaceDataRecord?format=json
        """
        import requests
        from requests.auth import HTTPDigestAuth
        import io

        url = f"{self.base_url}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
        
        # Metadata qismi
        face_data_json = json.dumps({
            "faceLibType": "blackFD",
            "FDID": "1",
            "FPID": str(employee_no)
        })

        files = {
            'FaceDataRecord': ('FaceDataRecord.json', face_data_json, 'application/json'),
            'img': ('face.jpg', image_bytes, 'image/jpeg')
        }

        try:
            resp = requests.post(
                url,
                files=files,
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=15
            )
            if resp.status_code in [200, 201]:
                return True, "Yuz rasmi terminalga muvaffaqiyatli yuklandi"
            
            # Agar yuz rasmi allaqachon mavjud bo'lsa
            if "deviceUserAlreadyExistFace" in resp.text:
                await self.delete_face(employee_no)
                resp_retry = requests.post(url, files=files, auth=HTTPDigestAuth(self.username, self.password), timeout=15)
                if resp_retry.status_code in [200, 201]:
                    return True, "Yuz rasmi muvaffaqiyatli yangilandi"
                return True, "Yuz rasmi allaqachon terminalda mavjud"

            # Agar birinchi endpoint mos kelmasa, AccessControl/FaceRecord ni sinab ko'ramiz
            alt_url = f"{self.base_url}/ISAPI/AccessControl/FaceRecord?format=json"
            alt_face_json = json.dumps({
                "FaceRecord": {
                    "employeeNo": str(employee_no),
                    "faceLibType": "blackFD"
                }
            })
            alt_files = {
                'FaceRecord': ('FaceRecord.json', alt_face_json, 'application/json'),
                'img': ('face.jpg', image_bytes, 'image/jpeg')
            }
            resp_alt = requests.post(
                alt_url,
                files=alt_files,
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=15
            )
            if resp_alt.status_code in [200, 201]:
                return True, "Yuz rasmi terminalga muvaffaqiyatli yuklandi"
            if "deviceUserAlreadyExistFace" in resp_alt.text:
                return True, "Yuz rasmi allaqachon terminalda mavjud"

            return False, format_isapi_error(resp.text, resp.status_code)
        except Exception as e:
            return False, f"Yuz rasmini yuklashda xatolik: {str(e)}"

    async def take_snapshot(self) -> Tuple[bool, Optional[bytes], str]:
        """
        Face ID terminali kamerasidan jonli foto snapshot olish.
        /ISAPI/Streaming/channels/101/picture yoki /ISAPI/Streaming/channels/1/picture
        """
        urls = [
            f"{self.base_url}/ISAPI/Streaming/channels/101/picture",
            f"{self.base_url}/ISAPI/Streaming/channels/1/picture"
        ]
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
                for u in urls:
                    try:
                        resp = await client.get(u)
                        if resp.status_code == 200 and len(resp.content) > 500:
                            return True, resp.content, "Snapshot muvaffaqiyatli olindi"
                    except Exception:
                        continue
                return False, None, "Terminal kamerasidan rasm olib bo'lmadi"
        except Exception as e:
            return False, None, f"Terminal bilan bog'lanishda xatolik: {str(e)}"

    async def get_all_users(self) -> Tuple[bool, list, str]:
        """
        Terminal xotirasidagi barcha xodimlarni o'qib olish (UserInfo/Search).
        """
        url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Search?format=json"
        all_users = []
        position = 0
        max_results = 30

        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=15.0) as client:
                headers = {"Content-Type": "application/json"}
                for _ in range(50): # Maksimal 1500 ta xodim
                    payload = {
                        "UserInfoSearchCond": {
                            "searchID": "1",
                            "searchResultPosition": position,
                            "maxResults": max_results
                        }
                    }
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code != 200:
                        break

                    try:
                        data = resp.json()
                        search_res = data.get("UserInfoSearch", {})
                        num_matches = search_res.get("numOfMatches", 0)
                        total_matches = search_res.get("totalMatches", 0)
                        raw_users = search_res.get("UserInfo", [])

                        if isinstance(raw_users, dict):
                            raw_users = [raw_users]

                        for u in raw_users:
                            emp_no = str(u.get("employeeNo", "")).strip()
                            name = u.get("name", "").strip() or f"Xodim #{emp_no}"
                            num_faces = u.get("numOfFace", 0)
                            face_url = u.get("faceURL")
                            if emp_no:
                                all_users.append({
                                    "employee_no": emp_no,
                                    "name": name,
                                    "user_type": u.get("userType", "normal"),
                                    "has_face": num_faces > 0 or bool(face_url),
                                    "face_url": face_url,
                                    "raw": u
                                })

                        if num_matches == 0 or len(all_users) >= total_matches or num_matches < max_results:
                            break
                        position += num_matches
                    except Exception as parse_err:
                        logger.warning(f"UserInfo JSON tahlilida xatolik: {parse_err}")
                        break

            return True, all_users, f"{len(all_users)} ta foydalanuvchi topildi"
        except Exception as e:
            return False, [], f"Terminaldan xodimlarni olishda xatolik: {str(e)}"

    async def get_face_picture(self, employee_no: str, face_url: Optional[str] = None) -> Tuple[bool, Optional[bytes], str]:
        """
        Terminaldan bitta xodimning yuz rasmini yuklab olish (faceURL, UserInfo yoki FDLib/FaceRecord).
        """
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=12.0) as client:
                # 1. Agar face_url tayyor berilgan bo'lsa
                if face_url:
                    full_url = face_url if face_url.startswith("http") else f"{self.base_url}{face_url if face_url.startswith('/') else '/' + face_url}"
                    try:
                        img_resp = await client.get(full_url)
                        if img_resp.status_code == 200 and len(img_resp.content) > 500:
                            return True, img_resp.content, "Yuz rasmi yuklab olindi"
                    except Exception as e:
                        logger.warning(f"Berilgan face_url dan yuklashda xatolik: {e}")

                # 2. UserInfo/Search orqali tekshirish (DS-K1T673T kabi yangi terminallarda yuz URL'i shu yerda bo'ladi)
                url_user_search = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Search?format=json"
                try:
                    pay_user = {
                        "UserInfoSearchCond": {
                            "searchID": "1",
                            "searchResultPosition": 0,
                            "maxResults": 1,
                            "EmployeeNoList": [{"employeeNo": str(employee_no)}]
                        }
                    }
                    ru = await client.post(url_user_search, json=pay_user, headers={"Content-Type": "application/json"})
                    if ru.status_code == 200:
                        u_list = ru.json().get("UserInfoSearch", {}).get("UserInfo", [])
                        if isinstance(u_list, dict): u_list = [u_list]
                        if u_list and u_list[0].get("faceURL"):
                            u_face_url = u_list[0]["faceURL"]
                            full_url = u_face_url if u_face_url.startswith("http") else f"{self.base_url}{u_face_url if u_face_url.startswith('/') else '/' + u_face_url}"
                            img_resp = await client.get(full_url)
                            if img_resp.status_code == 200 and len(img_resp.content) > 500:
                                return True, img_resp.content, "Yuz rasmi yuklab olindi"
                except Exception:
                    pass

                # 3. FDLib/FDSearch ni sinash
                url_fdsearch = f"{self.base_url}/ISAPI/Intelligent/FDLib/FDSearch?format=json"
                payload_fd = {
                    "FDLibSearchCond": {
                        "searchID": "1",
                        "searchResultPosition": 0,
                        "maxResults": 1,
                        "faceLibType": "blackFD",
                        "FDID": "1",
                        "employeeNo": str(employee_no)
                    }
                }
                try:
                    r1 = await client.post(url_fdsearch, json=payload_fd, headers={"Content-Type": "application/json"})
                    if r1.status_code == 200:
                        matches = r1.json().get("FDLibSearchResult", {}).get("MatchList", [])
                        if isinstance(matches, dict): matches = [matches]
                        if matches and matches[0].get("faceURL"):
                            f_url = matches[0]["faceURL"]
                            full_url = f_url if f_url.startswith("http") else f"{self.base_url}{f_url if f_url.startswith('/') else '/' + f_url}"
                            img_resp = await client.get(full_url)
                            if img_resp.status_code == 200 and len(img_resp.content) > 500:
                                return True, img_resp.content, "Yuz rasmi yuklab olindi"
                except Exception:
                    pass

                # 4. AccessControl/FaceRecord/Search ni sinash
                url_acsearch = f"{self.base_url}/ISAPI/AccessControl/FaceRecord/Search?format=json"
                payload_ac = {
                    "FaceRecordSearchCond": {
                        "searchID": "1",
                        "searchResultPosition": 0,
                        "maxResults": 1,
                        "faceLibType": "blackFD",
                        "employeeNo": str(employee_no)
                    }
                }
                try:
                    r2 = await client.post(url_acsearch, json=payload_ac, headers={"Content-Type": "application/json"})
                    if r2.status_code == 200:
                        data2 = r2.json().get("FaceRecordSearchResult", {})
                        matches2 = data2.get("MatchList", []) or data2.get("FaceRecord", [])
                        if isinstance(matches2, dict): matches2 = [matches2]
                        if matches2 and matches2[0].get("faceURL"):
                            f_url = matches2[0]["faceURL"]
                            full_url = f_url if f_url.startswith("http") else f"{self.base_url}{f_url if f_url.startswith('/') else '/' + f_url}"
                            img_resp = await client.get(full_url)
                            if img_resp.status_code == 200 and len(img_resp.content) > 500:
                                return True, img_resp.content, "Yuz rasmi yuklab olindi"
                except Exception:
                    pass

                return False, None, "Yuz rasmi URLi topilmadi"
        except Exception as e:
            return False, None, f"Rasm olishda xatolik: {str(e)}"

