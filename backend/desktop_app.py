import sys
import os
import base64
import ctypes

# GPU render tearing va oq qora bloklar xatoligini bartaraf etish hamda lokal terminal bridge uchun ruxsatlar
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing --disable-web-security --allow-running-insecure-content"

try:
    # Windows taskbar va oynalarda alohida dastur sifatida tanitish
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("burgood.accesscontrol.desktop.v2")
except Exception:
    pass

import subprocess
import time
import urllib.request
import threading
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import requests
from requests.auth import HTTPDigestAuth
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, 
    QMenu, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    parent1 = os.path.dirname(EXE_DIR)
    parent2 = os.path.dirname(parent1)
    if os.path.exists(os.path.join(EXE_DIR, "backend")):
        BASE_DIR = EXE_DIR
    elif os.path.exists(os.path.join(parent2, "backend")):
        BASE_DIR = parent2
    elif os.path.exists(r"D:\BurgoodAccsesCantrol\backend"):
        BASE_DIR = r"D:\BurgoodAccsesCantrol"
    else:
        BASE_DIR = EXE_DIR
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def apply_dark_title_bar(window):
    """Windows 10 va 11 da Title Bar'ni Burgood brend rangi (#0084ff) va oq matnga aylantirish"""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        DWMWA_CAPTION_COLOR = 35 # Windows 11 BGR: 0x00FF8400 (#0084ff Burgood Blue)
        DWMWA_TEXT_COLOR = 36    # Windows 11 BGR: 0x00FFFFFF (Oq matn)
        
        # 1. Windows 11 da sarlavha fonini to'g'ridan-to'g'ri #0084ff va matnni oppoq qilish
        bg_color = ctypes.c_int(0x00FF8400)
        res_cap = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(bg_color), ctypes.sizeof(bg_color)
        )
        text_color = ctypes.c_int(0x00FFFFFF)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_color), ctypes.sizeof(text_color)
        )

        # 2. Windows 10 uchun fallback (agar maxsus rang qo'llab-quvvatlanmasa dark mode)
        if res_cap != 0:
            val = ctypes.c_int(1)
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val)
            )
            if res != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ctypes.byref(val), ctypes.sizeof(val)
                )
    except Exception:
        pass

def get_app_icon():
    """Har qanday kompyuterda (PyInstaller yoki begona tizimda) 100% kafolat bilan Burgood ikonkasini olish"""
    candidates = []
    
    # 1. PyInstaller MEIPASS vaqtincha papkasi (boshqa kompyuterlarda shu ishlaydi)
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.extend([
                os.path.join(meipass, "frontend", "public", "app_icon.ico"),
                os.path.join(meipass, "frontend", "public", "burgood_shield.png"),
                os.path.join(meipass, "app_icon.ico"),
                os.path.join(meipass, "burgood_shield.png"),
            ])
        exe_dir = os.path.dirname(sys.executable)
        candidates.extend([
            os.path.join(exe_dir, "app_icon.ico"),
            os.path.join(exe_dir, "burgood_shield.png"),
            os.path.join(exe_dir, "frontend", "public", "app_icon.ico"),
        ])
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.extend([
            os.path.join(base, "frontend", "public", "app_icon.ico"),
            os.path.join(base, "frontend", "public", "burgood_shield.png"),
            os.path.join(base, "frontend", "public", "favicon.ico"),
        ])

    for path in candidates:
        if path and os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon, path

    # 2. Ichki (Embedded) Base64 orqali yuklash (fayl mutlaqo topilmaganda ham 100% ishlaydi)
    try:
        try:
            from icon_data import APP_ICON_B64
        except ImportError:
            from backend.icon_data import APP_ICON_B64
        data = base64.b64decode(APP_ICON_B64)
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            icon_dir = os.path.join(local_appdata, "BurgoodAccessControl")
            os.makedirs(icon_dir, exist_ok=True)
            saved_ico = os.path.join(icon_dir, "app_icon.ico")
            try:
                with open(saved_ico, "wb") as f:
                    f.write(data)
            except Exception:
                pass
            return QIcon(pix), saved_ico
    except Exception:
        pass

    return QIcon(), ""

class WebEnginePage(QWebEnginePage):
    """Kamera va bildirishnomalarga avtomatik ruxsat berish"""
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

    def onFeaturePermissionRequested(self, securityOrigin, feature):
        # MediaAudioCapture, MediaVideoCapture, Notifications ga avtomatik ruxsat
        self.setFeaturePermission(
            securityOrigin, 
            feature, 
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        )

class BurgoodMainWindow(QMainWindow):
    def __init__(self, icon=None, icon_path=""):
        super().__init__()
        self.app_icon = icon if icon else QIcon()
        self.icon_path = icon_path
        self.setWindowTitle("Burgood Access Control — Face ID & Davomat Tizimi")
        self.resize(1300, 850)
        self.setMinimumSize(1024, 680)

        # Ikonka o'rnatish
        if not self.app_icon.isNull():
            self.setWindowIcon(self.app_icon)
        elif self.icon_path and os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        # Windows sarlavhasini (Title Bar) chiroyli to'q ko'k (#0a1122) rangga o'tkazish
        apply_dark_title_bar(self)

        # Ish stoliga (Desktop) avtomatik yorliq chiqarish
        self.ensure_desktop_shortcut()

        # WebView va doimiy profil yaratish (Login seansi va sozlamalarni xotirada eslab qolish)
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        storage_base = os.path.join(local_appdata, "BurgoodAccessControl")
        profile_dir = os.path.join(storage_base, "WebProfile")
        cache_dir = os.path.join(storage_base, "WebCache")
        os.makedirs(profile_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

        self.profile = QWebEngineProfile("BurgoodProfile", self)
        self.profile.setPersistentStoragePath(profile_dir)
        self.profile.setCachePath(cache_dir)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        
        self.page = WebEnginePage(self.profile, self)
        self.webview = QWebEngineView(self)
        self.webview.setPage(self.page)
        self.setCentralWidget(self.webview)

        # Server manzilini aniqlash:
        # Asosiy markaziy server - Cloud VPS (Barcha terminallar, botlar va yangi foydalanuvchilar shu yerda)
        cloud_url = "https://44.221.176.109.sslip.io"
        app_url = cloud_url

        self.webview.setUrl(QUrl(app_url))

        # F5 va Ctrl+R orqali tezkor yangilash
        QShortcut(QKeySequence("F5"), self, self.webview.reload)
        QShortcut(QKeySequence("Ctrl+R"), self, self.webview.reload)

        # Tizim treyi (System Tray) yaratish
        self.setup_tray()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def ensure_desktop_shortcut(self):
        """Dastur bir marta ishga tushganda ham Ish stoliga (Desktop) avtomatik yorliq yaratish"""
        try:
            exe_path = sys.executable
            if not getattr(sys, 'frozen', False):
                return
            work_dir = os.path.dirname(exe_path)
            icon_arg = self.icon_path if (self.icon_path and os.path.exists(self.icon_path)) else f"{exe_path},0"
            ps_cmd = (
                f"$dt = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::DesktopDirectory); "
                f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut(\\\"$dt\\Burgood Access Control.lnk\\\"); "
                f"$s.TargetPath = \\\"{exe_path}\\\"; "
                f"$s.WorkingDirectory = \\\"{work_dir}\\\"; "
                f"$s.IconLocation = \\\"{icon_arg}\\\"; "
                f"$s.Description = 'Burgood Access Control - Face ID & Davomat'; "
                f"$s.Save()"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                creationflags=0x08000000,
                timeout=4
            )
        except Exception:
            pass

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        if hasattr(self, 'app_icon') and not self.app_icon.isNull():
            self.tray.setIcon(self.app_icon)
        elif hasattr(self, 'icon_path') and self.icon_path and os.path.exists(self.icon_path):
            self.tray.setIcon(QIcon(self.icon_path))

        tray_menu = QMenu()
        open_action = tray_menu.addAction("🖥 Dasturni ochish")
        open_action.triggered.connect(self.show_and_activate)

        reload_action = tray_menu.addAction("🔄 Qayta yuklash")
        reload_action.triggered.connect(self.webview.reload)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("🚪 Tizimdan chiqish")
        quit_action.triggered.connect(self.really_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_activate()

    def show_and_activate(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Burgood Access Control",
            "Dasturni butunlay yopmoqchimisiz yoki fonda (Tray) qoldirmoqchimisiz?\n\n"
            "• 'Yes' - Dasturni yopish\n"
            "• 'No' - Fonda ishlashda davom etish (Kuzatuv to'xtamaydi)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "Burgood Access Control",
                "Dastur fonda ishlamoqda. Turniketlar va Telegram botlar faol.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def really_quit(self):
        QApplication.quit()

def pull_terminal_users_local(ip, port, username, password, server_url, token):
    """Lokal tarmoqdagi Hikvision Face ID terminalidan xodimlarni va ularning yuz rasmlarini o'qib bulutga uzatish"""
    base_url = f"http://{ip}:{port}"
    auth = HTTPDigestAuth(username, password)
    
    # 1. UserInfo/Search
    url_search = f"{base_url}/ISAPI/AccessControl/UserInfo/Search?format=json"
    users_to_import = []
    position = 0
    max_results = 30
    
    for _ in range(50):
        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": position,
                "maxResults": max_results
            }
        }
        try:
            r = requests.post(url_search, json=payload, auth=auth, timeout=12)
            if r.status_code != 200:
                break
            res_data = r.json().get("UserInfoSearch", {})
            num_matches = res_data.get("numOfMatches", 0)
            total_matches = res_data.get("totalMatches", 0)
            raw_users = res_data.get("UserInfo", [])
            if isinstance(raw_users, dict):
                raw_users = [raw_users]
            
            for u in raw_users:
                emp_no = str(u.get("employeeNo", "")).strip()
                name = str(u.get("name", "")).strip() or f"Xodim #{emp_no}"
                num_face = u.get("numOfFace", 0)
                face_url = u.get("faceURL")
                if emp_no:
                    users_to_import.append({
                        "employee_no": emp_no,
                        "name": name,
                        "has_face": num_face > 0 or bool(face_url),
                        "face_url": face_url,
                        "photo_base64": None
                    })
            if num_matches == 0 or len(users_to_import) >= total_matches or num_matches < max_results:
                break
            position += num_matches
        except Exception:
            break

    if not users_to_import:
        return {"success": False, "message": "Terminaldan xodimlar topilmadi yoki ulanishda xatolik yuz berdi. IP, port va parolni tekshiring."}

    # 2. Yuz rasmlarini yuklab olish
    faces_downloaded = 0
    for u in users_to_import:
        if u["has_face"]:
            emp_no = u["employee_no"]
            face_url = u.get("face_url")
            
            # Agar face_url mavjud bo'lmasa, qidirish
            if not face_url:
                try:
                    f_url = f"{base_url}/ISAPI/Intelligent/FDLib/FDSearch?format=json"
                    f_pay = {
                        "FDLibSearchCond": {
                            "searchID": "1", "searchResultPosition": 0, "maxResults": 1,
                            "faceLibType": "blackFD", "FDID": "1", "employeeNo": emp_no
                        }
                    }
                    fr = requests.post(f_url, json=f_pay, auth=auth, timeout=6)
                    if fr.status_code == 200:
                        m = fr.json().get("FDLibSearchResult", {}).get("MatchList", [])
                        if isinstance(m, dict): m = [m]
                        if m and m[0].get("faceURL"):
                            face_url = m[0]["faceURL"]
                except Exception:
                    pass
            
            if not face_url:
                try:
                    ac_url = f"{base_url}/ISAPI/AccessControl/FaceRecord/Search?format=json"
                    ac_pay = {
                        "FaceRecordSearchCond": {
                            "searchID": "1", "searchResultPosition": 0, "maxResults": 1,
                            "faceLibType": "blackFD", "employeeNo": emp_no
                        }
                    }
                    acr = requests.post(ac_url, json=ac_pay, auth=auth, timeout=6)
                    if acr.status_code == 200:
                        d2 = acr.json().get("FaceRecordSearchResult", {})
                        m2 = d2.get("MatchList", []) or d2.get("FaceRecord", [])
                        if isinstance(m2, dict): m2 = [m2]
                        if m2 and m2[0].get("faceURL"):
                            face_url = m2[0]["faceURL"]
                except Exception:
                    pass

            if face_url:
                try:
                    if face_url.startswith("/"):
                        face_url = f"{base_url}{face_url}"
                    ir = requests.get(face_url, auth=auth, timeout=8)
                    if ir.status_code == 200 and len(ir.content) > 500:
                        u["photo_base64"] = base64.b64encode(ir.content).decode('utf-8')
                        faces_downloaded += 1
                except Exception:
                    pass

    # 3. Serverga (Cloud) yuborish
    upload_url = f"{server_url.rstrip('/')}/api/v1/users/batch-import-with-faces"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        cloud_resp = requests.post(upload_url, json={"users": users_to_import}, headers=headers, timeout=60)
        if cloud_resp.status_code == 200:
            res_json = cloud_resp.json()
            res_json["faces_downloaded_from_device"] = faces_downloaded
            return res_json
        else:
            return {"success": False, "message": f"Serverga saqlashda xatolik: {cloud_resp.text}"}
    except Exception as e:
        return {"success": False, "message": f"Server bilan aloqa xatosi: {str(e)}"}

class LocalTerminalBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","bridge":"BurgoodLocalBridge"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/test-terminal":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                ip = data.get("ip", "")
                port = int(data.get("port", 80))
                username = data.get("username", "admin")
                password = data.get("password", "")
                
                url = f"http://{ip}:{port}/ISAPI/System/deviceInfo"
                auth = HTTPDigestAuth(username, password)
                r = requests.get(url, auth=auth, timeout=4)
                if r.status_code == 200:
                    res = {"success": True, "message": "Terminal bilan lokal aloqa muvaffaqiyatli bog'landi!"}
                else:
                    res = {"success": False, "message": f"Terminal javob berdi: Status {r.status_code}"}
            except Exception as e:
                res = {"success": False, "message": f"Lokal ulanishda xato: {str(e)}"}
            
            resp_bytes = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        if self.path == "/api/pull-terminal":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                ip = data.get("ip", "")
                port = int(data.get("port", 80))
                username = data.get("username", "admin")
                password = data.get("password", "")
                server_url = data.get("server_url", "https://44.221.176.109.sslip.io")
                token = data.get("token", "")

                result = pull_terminal_users_local(ip, port, username, password, server_url, token)
                
                resp_bytes = json.dumps(result).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Private-Network", "true")
                self.end_headers()
                self.wfile.write(resp_bytes)
            except Exception as e:
                err_resp = json.dumps({"success": False, "message": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Private-Network", "true")
                self.end_headers()
                self.wfile.write(err_resp)
        else:
            self.send_response(404)
            self.end_headers()

def start_local_bridge():
    try:
        server = ThreadingHTTPServer(('127.0.0.1', 18200), LocalTerminalBridgeHandler)
        server.daemon_threads = True
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
    except Exception as e:
        print("Local bridge start failed:", e)

def check_server(url="http://127.0.0.1:8000"):
    try:
        req = urllib.request.Request(f"{url}/docs", headers={"User-Agent": "BurgoodDesktop/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as r:
            return r.status == 200
    except Exception:
        return False

def ensure_backend_running():
    if not check_server():
        try:
            backend_dir = os.path.join(BASE_DIR, "backend")
            python_cmd = "python"
            if not getattr(sys, 'frozen', False):
                python_cmd = sys.executable

            subprocess.Popen(
                [python_cmd, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=backend_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            for _ in range(25):
                if check_server():
                    break
                time.sleep(0.3)
        except Exception as e:
            print(f"Serverni ishga tushirishda xato: {e}")

def main():
    # Faqat lokal turniket ko'prigini ishga tushirish (127.0.0.1:18200)
    start_local_bridge()
    app = QApplication(sys.argv)
    app.setOrganizationName("Burgood")
    app.setOrganizationDomain("burgood.uz")
    app.setApplicationName("BurgoodAccessControl")
    
    app_icon, ico_path = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    elif ico_path and os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))

    window = BurgoodMainWindow(app_icon, ico_path)
    window.show()
    apply_dark_title_bar(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
