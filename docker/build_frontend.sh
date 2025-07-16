#!/bin/bash

# Установить режим строгой обработки ошибок
set -e

echo "=== Starting frontend build ==="

# Перейти в директорию frontend
cd frontend

echo "=== Cleaning up previous build ==="
# Очистить предыдущие установки и кеши
rm -rf node_modules package-lock.json
rm -rf ~/.npm/_cacache 2>/dev/null || true

echo "=== Installing dependencies ==="
# Установить зависимости с чистого листа
npm cache clean --force
npm install

echo "=== Installing missing dependencies ==="
# Установить отсутствующие зависимости
npm install vue-i18n || echo "vue-i18n already installed or failed to install"

echo "=== Building frontend ==="
# Собрать проект
npm run build

# Проверить, что сборка прошла успешно
if [ ! -d "dist" ]; then
    echo "ERROR: Build failed - dist directory not created"
    exit 1
fi

echo "=== Creating .htaccess file ==="
# Создать .htaccess файл
BUILD_DIR="/home/deploy/SmartClause/frontend/dist"

# Убедиться, что директория существует
if [ ! -d "$BUILD_DIR" ]; then
    echo "ERROR: Build directory $BUILD_DIR does not exist"
    exit 1
fi

# Создать .htaccess файл
cat > "$BUILD_DIR/.htaccess" <<EOF
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteRule ^index\.html$ - [L]
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /index.html [L]
</IfModule>
EOF

# Проверить, что .htaccess создан
if [ ! -f "$BUILD_DIR/.htaccess" ]; then
    echo "ERROR: Failed to create .htaccess file"
    exit 1
fi

echo "=== Frontend build completed successfully ==="
