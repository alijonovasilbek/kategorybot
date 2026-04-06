#!/bin/bash
# deploy.sh — VPS ga deploy qilish skripti
# Ishlatish: bash deploy.sh

set -e

DOMAIN="your-domain.com"
APP_DIR="/var/www/kategorybot"
REPO="https://github.com/alijonovasilbek/kategorybot.git"
WEBAPP_DIR="$APP_DIR/webapp"
NGINX_DIR="/etc/nginx/sites-available"

echo "🚀 KategoryBot deploy boshlandi..."

# 1. Zarur paketlarni o'rnatish
echo "📦 Paketlar o'rnatilmoqda..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# 2. Reponi klonlash yoki yangilash
if [ -d "$APP_DIR" ]; then
    echo "🔄 Repo yangilanmoqda..."
    cd $APP_DIR && git pull
else
    echo "📥 Repo yuklanmoqda..."
    git clone $REPO $APP_DIR
fi
cd $APP_DIR

# 3. Virtual environment
echo "🐍 Python venv sozlanmoqda..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q

# 4. .env fayli
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  .env fayli yaratildi! To'ldiring: nano $APP_DIR/.env"
fi

# 5. Ma'lumotlar bazasini yaratish
echo "🗄️  Ma'lumotlar bazasi sozlanmoqda..."
python3 -c "import asyncio; from database.db import init_db; asyncio.run(init_db())"

# 6. Nginx konfiguratsiya
echo "🌐 Nginx sozlanmoqda..."
sed "s/YOUR_DOMAIN.com/$DOMAIN/g" nginx.conf.example > /etc/nginx/sites-available/kategorybot
ln -sf /etc/nginx/sites-available/kategorybot /etc/nginx/sites-enabled/kategorybot
nginx -t && systemctl reload nginx

# 7. SSL sertifikat
echo "🔒 SSL sertifikat olinmoqda..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || echo "⚠️  SSL qo'lda o'rnatilishi kerak"

# 8. Systemd service
echo "⚙️  Systemd service o'rnatilmoqda..."
cp kategorybot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kategorybot
systemctl restart kategorybot

echo ""
echo "✅ Deploy muvaffaqiyatli yakunlandi!"
echo "   🌐 WebApp: https://$DOMAIN"
echo "   ⚙️  Admin:  https://$DOMAIN/admin"
echo "   📊 API:    https://$DOMAIN/api/products"
echo ""
echo "   Navbatdagi qadamlar:"
echo "   1. nano $APP_DIR/.env  (BOT_TOKEN va WEBAPP_URL ni kiriting)"
echo "   2. systemctl restart kategorybot"
echo "   3. python3 $APP_DIR/seed.py  (demo ma'lumotlar uchun)"
