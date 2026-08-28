#!/bin/bash
# ==============================================================================
# Saint Demiana Retreat Management System - Production Deployment Script
# Designed for Oracle Cloud Always Free (Ubuntu 22.04 / 24.04 LTS / Debian)
# ==============================================================================

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
GOLD='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GOLD}"
echo "======================================================================"
echo "   ✝ نظام إدارة بيت الخلوة - دير القديسة دميانة ببراري بلقاس ✝"
echo "        البرنامج التلقائي لإعداد ونشر السيرفر السحابي (Production)"
echo "======================================================================"
echo -e "${NC}"

# Check for root / sudo privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] يرجى تشغيل السكربت بصلاحيات المدير (sudo ./setup_production.sh)${NC}"
  exit 1
fi

APP_DIR="/var/www/demiana-retreat-system"
CURRENT_DIR=$(pwd)
APP_USER="www-data"

echo -e "${CYAN}[1/8] تحديث حزم النظام وتثبيت المتطلبات الأساسية...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-pip python3-venv python3-dev \
    build-essential libssl-dev libffi-dev \
    nginx certbot python3-certbot-nginx \
    ufw git curl sqlite3 \
    fonts-dejavu fonts-freefont-ttf libfreetype6-dev libjpeg-dev

echo -e "${CYAN}[2/8] تجهيز مسار التطبيق ونقل الملفات...${NC}"
mkdir -p "${APP_DIR}"
mkdir -p "${APP_DIR}/data"
mkdir -p "${APP_DIR}/uploads"
mkdir -p "${APP_DIR}/logs"

# Copy files if running outside /var/www/demiana-retreat-system
if [ "${CURRENT_DIR}" != "${APP_DIR}" ]; then
  echo "جاري نسخ ملفات المشروع إلى ${APP_DIR}..."
  cp -r "${CURRENT_DIR}"/* "${APP_DIR}/"
fi

cd "${APP_DIR}"

echo -e "${CYAN}[3/8] إعداد بيئة بايثون الافتراضية وتثبيت المكتبات...${NC}"
if [ ! -d "${APP_DIR}/.venv" ]; then
  python3 -m venv "${APP_DIR}/.venv"
fi

"${APP_DIR}/.venv/bin/pip" install --upgrade pip setuptools wheel
"${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo -e "${CYAN}[4/8] ضبط ملف الإعدادات والبيئة (.env)...${NC}"
if [ ! -f "${APP_DIR}/.env" ]; then
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  cat <<EOF > "${APP_DIR}/.env"
# Saint Demiana Production Configuration
ENVIRONMENT=production
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
DATABASE_URL=sqlite+aiosqlite:///${APP_DIR}/data/demiana.db
UPLOAD_DIR=${APP_DIR}/uploads
MAX_FILE_SIZE_BYTES=10485760

# SMTP Email Configuration (Gmail App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=586
SMTP_USER=st.demiana.retreat@gmail.com
SMTP_PASSWORD=put_your_gmail_app_password_here
SMTP_FROM_EMAIL=st.demiana.retreat@gmail.com
SMTP_FROM_NAME=بيت الخلوة بدير القديسة دميانة

# Default Seed Superuser Credentials
SUPERUSER_EMAIL=mother.superior@demiana.org
SUPERUSER_PASSWORD=Demiana@2026#Monastery
SUPERUSER_PHONE=01000000000
EOF
  echo -e "${GREEN}[OK] تم إنشاء ملف .env بمفتاح تشفير آمن.${NC}"
else
  echo "ملف .env موجود بالفعل، تم الاحتفاظ به."
fi

# Set proper ownership and permissions
chown -R ${APP_USER}:${APP_USER} "${APP_DIR}"
chmod -R 755 "${APP_DIR}"
chmod -R 775 "${APP_DIR}/data" "${APP_DIR}/uploads" "${APP_DIR}/logs"

echo -e "${CYAN}[5/8] إعداد خدمة التشغيل التلقائي (Systemd Service)...${NC}"
cat <<EOF > /etc/systemd/system/demiana.service
[Unit]
Description=Saint Demiana Monastery Retreat System (FastAPI Production Daemon)
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${APP_DIR}/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
Restart=always
RestartSec=5
StandardOutput=append:${APP_DIR}/logs/app.log
StandardError=append:${APP_DIR}/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable demiana.service
systemctl restart demiana.service

echo -e "${CYAN}[6/8] ضبط خادم الويب Nginx...${NC}"
cat <<EOF > /etc/nginx/sites-available/demiana
server {
    listen 80;
    listen [::]:80;
    server_name _;

    client_max_body_size 50M;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss image/svg+xml;

    # Static Assets Cache
    location /static/ {
        alias ${APP_DIR}/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Reverse Proxy to FastAPI Uvicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF

# Enable Nginx configuration
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/demiana /etc/nginx/sites-enabled/demiana
nginx -t && systemctl restart nginx

echo -e "${CYAN}[7/8] فتح منافذ الجدار الناري في Oracle Cloud (Port 80 & 443)...${NC}"
# Oracle Linux/Ubuntu default iptables rules fix
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
netfilter-persistent save 2>/dev/null || true

# UFW rules
ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
echo "y" | ufw enable || true

echo -e "${CYAN}[8/8] إنشاء أداة الإدارة السريعة (demiana-ctl)...${NC}"
cat <<'EOF' > /usr/local/bin/demiana-ctl
#!/bin/bash
case "$1" in
    status)
        systemctl status demiana.service
        ;;
    restart)
        systemctl restart demiana.service
        echo "تمت إعادة تشغيل الخدمة بنجاح."
        ;;
    logs)
        journalctl -u demiana.service -f
        ;;
    backup)
        BACKUP_FILE="/var/www/demiana-retreat-system/data/backup_$(date +%Y%m%d_%H%M%S).db"
        sqlite3 /var/www/demiana-retreat-system/data/demiana.db ".backup ${BACKUP_FILE}"
        echo "تم أخذ نسخة احتياطية لقاعدة البيانات في: ${BACKUP_FILE}"
        ;;
    ssl)
        read -p "أدخل اسم النطاق (Domain Name) الخاص بك (مثال: retreat.demiana.org): " DOMAIN
        certbot --nginx -d "${DOMAIN}"
        ;;
    *)
        echo "الاستخدام: demiana-ctl {status|restart|logs|backup|ssl}"
        exit 1
        ;;
esac
EOF
chmod +x /usr/local/bin/demiana-ctl

PUBLIC_IP=$(curl -s https://api.ipify.org || echo "IP_السيرفر_الخاص_بك")

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}       ✨ تم تثبيت وتشغيل نظام بيت الخلوة بنجاح 100%! ✨${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "🌐 يمكنك الدخول على النظام الآن عبر المتصفح باستخدام الرابط:"
echo -e "   ${GOLD}http://${PUBLIC_IP}${NC}"
echo ""
echo -e "🔑 بيانات الدخول الافتراضية للأم المسؤولة:"
echo -e "   البريد:    ${CYAN}mother.superior@demiana.org${NC}"
echo -e "   كلمة السر: ${CYAN}Demiana@2026#Monastery${NC}"
echo ""
echo -e "🛠 أوامر الإدارة السريعة للسيرفر:"
echo -e "   - متابعة السجلات المباشرة:    ${GOLD}demiana-ctl logs${NC}"
echo -e "   - إعادة تشغيل النظام:         ${GOLD}demiana-ctl restart${NC}"
echo -e "   - أخذ نسخة احتياطية للبيانات: ${GOLD}demiana-ctl backup${NC}"
echo -e "   - تفعيل شهادة SSL/HTTPS:     ${GOLD}demiana-ctl ssl${NC}"
echo ""
echo -e "${GOLD}✝ بركة وشفاعة القديسة دميانة تشمل هذا العمل المبارك ✝${NC}"
