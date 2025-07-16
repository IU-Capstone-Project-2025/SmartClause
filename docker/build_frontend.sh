cd frontend
npm install
npm run build
BUILD_DIR="/home/deploy/SmartClause/frontend/dist"
cat > "$BUILD_DIR/.htaccess" <<EOF
RewriteEngine On
RewriteBase /
RewriteRule ^index\.html$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]
EOF