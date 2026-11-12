# BURGOOD LOYIHALARINI MUTLAQO BIR-BIRIDAN AJRATISH QOIDALARI (DEVOR ARXITEKTURASI)

Ushbu serverda va ishchi muhitda 2 ta mustaqil loyiha mavjud:

## 1. BURGOOD SHOP (Online Do'kon)
* **Domen:** `https://burgoodshop.uz` va `https://www.burgoodshop.uz`
* **Bot:** `@Burgood_shop_bot`
* **Serverdagi katalogi:** `/home/ubuntu/burgood_shop/`
* **Backend porti:** `127.0.0.1:8001`
* **Xizmati:** `burgood_shop.service`
* **Nginx konfiguratsiyasi:** `/etc/nginx/sites-available/burgood_shop.conf`

## 2. BURGOOD ACCESS CONTROL (Turniket & Davomat Tizimi)
* **Domen:** `https://44.221.176.109.sslip.io`
* **Botlar:** `@BurgoodAccsesCantrolMaster_bot` va `@BurgoodAccsesCantrol_bot`
* **Serverdagi katalogi:** `/home/ubuntu/access_control/` va `/home/ubuntu/burgood/frontend/dist`
* **Backend porti:** `127.0.0.1:8000`
* **Xizmati:** `access_control.service`
* **Nginx konfiguratsiyasi:** `/etc/nginx/sites-available/access_control.conf`

---

## ⛔ QAT'IY QOIDALAR (BUZILISHI TAQIQLANADI):
1. **Hech qachon umumiy yoki bitta Nginx fayliga birlashtirilmasin!** Har bir loyiha faqat o'zining `.conf` faylida yashaydi.
2. **Access Control ustida ishlayotganda:** Faqat `access_control.conf`, `access_control.service`, port `8000` va uning fayllari bilan ishlanadi. `burgood_shop` fayllari, port `8001` va `burgoodshop.uz` ga teginish MUTLAQO TAQIQLANADI.
3. **Burgood Shop ustida ishlayotganda:** Faqat `burgood_shop.conf`, `burgood_shop.service`, port `8001` va uning fayllari bilan ishlanadi. `access_control` fayllari va port `8000` ga teginish MUTLAQO TAQIQLANADI.
4. Nginx `root` manzillari hech qachon aralashtirilmasin.
