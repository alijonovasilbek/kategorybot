# 🛍️ KategoryBot — Telegram WebApp Do'kon Boti

Universal mahsulot do'koni boti. Kiyim-kechak, oziq-ovqat va har qanday kategoriya uchun mos.

---

## 📁 Loyiha tuzilmasi

```
kategorybot/
├── bot/
│   ├── main.py          # Botni ishga tushirish
│   ├── handlers.py      # Telegram handler-lar
│   └── config.py        # Sozlamalar
├── database/
│   ├── db.py            # SQLAlchemy modellari
│   └── crud.py          # Ma'lumotlar bazasi operatsiyalari
├── webapp/
│   ├── index.html       # Asosiy WebApp (do'kon)
│   └── admin.html       # Admin panel
├── api.py               # FastAPI backend
├── requirements.txt
├── .env.example
└── start.sh
```

---

## 🚀 O'rnatish va ishga tushirish

### 1. Talablarni o'rnatish
```bash
pip install -r requirements.txt
```

### 2. Muhit sozlamalari
```bash
cp .env.example .env
# .env faylini tahrirlang:
nano .env
```

`.env` faylida to'ldiring:
```env
BOT_TOKEN=@BotFather dan olingan token
WEBAPP_URL=https://sizning-domen.com
ADMIN_IDS=sizning_telegram_id
DATABASE_URL=sqlite+aiosqlite:///./shop.db
```

### 3. WebApp fayllarini API bilan ulash
`webapp/index.html` va `webapp/admin.html` fayllarida `const API = '';` qatorini tekshiring.

### 4. Ishga tushirish
```bash
chmod +x start.sh
./start.sh
```

Yoki alohida:
```bash
# Terminal 1: Bot
cd bot && python main.py

# Terminal 2: API + WebApp
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🌐 Deploy (Production)

### Nginx konfiguratsiyasi
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location / {
        root /path/to/kategorybot/webapp;
        try_files $uri $uri/ /index.html;
    }

    location /admin {
        root /path/to/kategorybot/webapp;
        try_files /admin.html =404;
    }
}
```

### SSL (Let's Encrypt)
```bash
certbot --nginx -d your-domain.com
```

> **Muhim:** Telegram WebApp HTTPS talab qiladi!

---

## ⚙️ Xususiyatlar

### 👤 Foydalanuvchi
- Telegram orqali ro'yxatdan o'tish (telefon raqam)
- O'zbek / Rus tili
- Kategoriyalar (scrollable)
- Mahsulotlar (2 ta rowda)
- Mahsulot detali + 4 ta rasm galereyasi
- O'xshash mahsulotlar
- Qidirish
- Savatcha
- Xaritadan manzil tanlash (OpenStreetMap)
- Buyurtmalar tarixi
- Profil

### ⚙️ Admin (`/admin` buyrug'i)
- Dashboard (statistika)
- Kategoriya qo'shish/tahrirlash/o'chirish (rasm bilan)
- Mahsulot qo'shish/tahrirlash/o'chirish (4 ta rasm)
- Buyurtmalar va status o'zgartirish
- Foydalanuvchilar ro'yxati

---

## 📱 Bot buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/lang` | Tilni o'zgartirish |
| `/admin` | Admin panel (faqat adminlar uchun) |

---

## 🔗 API Endpointlar

| Method | Endpoint | Tavsif |
|--------|----------|--------|
| GET | `/api/categories` | Kategoriyalar |
| POST | `/api/categories` | Kategoriya qo'shish |
| GET | `/api/products` | Mahsulotlar |
| GET | `/api/products/{id}/similar` | O'xshash mahsulotlar |
| GET | `/api/cart/{user_id}` | Savatcha |
| POST | `/api/cart` | Savatchaga qo'shish |
| POST | `/api/orders` | Buyurtma berish |
| GET | `/api/admin/orders` | Barcha buyurtmalar |

---

## 🎨 Universal Bo'lishi

Bot istalgan turdagi do'kon uchun mos:
- **Kiyim-kechak:** Kategoriyalar: Erkaklar, Ayollar, Bolalar
- **Oziq-ovqat:** Kategoriyalar: Sabzavotlar, Mevalar, Go'sht
- **Elektronika:** Kategoriyalar: Telefonlar, Noutbuklar
- **Dorixona:** Kategoriyalar: Dorilar, Vitaminar

Faqat Admin panelidan kategoriya va mahsulot qo'shing!
