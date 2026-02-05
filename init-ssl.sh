#!/bin/bash

# SSL Certificate Setup Script for ksar.geniura.com

DOMAIN="ksar.geniura.com"
EMAIL="admin@geniura.com"

echo "=== إعداد شهادة SSL لـ $DOMAIN ==="

# إنشاء المجلدات المطلوبة
mkdir -p certbot/conf certbot/www

# استخدام nginx-init.conf مؤقتاً (بدون SSL)
cp nginx-init.conf nginx-temp.conf

# تشغيل الخدمات بدون SSL أولاً
echo "=== تشغيل الخدمات بدون SSL ==="
docker-compose down 2>/dev/null

# تعديل docker-compose مؤقتاً لاستخدام nginx-init
sed 's/nginx.conf/nginx-init.conf/g' docker-compose.yml > docker-compose-init.yml

docker-compose -f docker-compose-init.yml up -d db redis backend

echo "=== انتظار تشغيل الخدمات ==="
sleep 10

# تشغيل nginx بالإعدادات الأولية
docker-compose -f docker-compose-init.yml up -d nginx

echo "=== انتظار nginx ==="
sleep 5

# الحصول على شهادة SSL
echo "=== الحصول على شهادة SSL ==="
docker-compose -f docker-compose-init.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# التحقق من نجاح الحصول على الشهادة
if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "=== تم الحصول على الشهادة بنجاح! ==="
    
    # إيقاف الخدمات
    docker-compose -f docker-compose-init.yml down
    
    # تشغيل مع SSL
    echo "=== تشغيل الخدمات مع SSL ==="
    docker-compose up -d
    
    echo "=== تم! الموقع متاح على https://$DOMAIN ==="
else
    echo "=== فشل الحصول على الشهادة ==="
    echo "=== الموقع متاح على http://$DOMAIN (بدون SSL) ==="
    
    # الاستمرار بدون SSL
    docker-compose -f docker-compose-init.yml down
    
    # استخدام nginx-init كملف رئيسي
    cp nginx-init.conf nginx.conf
    docker-compose up -d
fi

# تنظيف
rm -f docker-compose-init.yml nginx-temp.conf

echo "=== انتهى الإعداد ==="
