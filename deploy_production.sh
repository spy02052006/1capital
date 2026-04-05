#!/bin/bash
# Production deployment setup for 1capital.in
# This configures Gunicorn + Nginx to make the dashboard accessible on your domain

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   PRODUCTION DEPLOYMENT SETUP FOR 1CAPITAL.IN                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"

DASHBOARD_DIR="/var/www/SalesDashboardProject/SalesDashboard"
VENV_DIR="/var/www/SalesDashboardProject/venv"

echo ""
echo "[STEP 1] Installing production server (Gunicorn)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Install gunicorn if not present
if ! pip list | grep -q gunicorn; then
    pip install gunicorn
    echo "✓ Gunicorn installed"
else
    echo "✓ Gunicorn already installed"
fi

echo ""
echo "[STEP 2] Collecting static files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$DASHBOARD_DIR"
python manage.py collectstatic --noinput
echo "✓ Static files collected"

echo ""
echo "[STEP 3] Creating Gunicorn socket and service files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create gunicorn socket file
sudo tee /etc/systemd/system/gunicorn-dashboard.socket > /dev/null << 'EOF'
[Unit]
Description=gunicorn dashboard socket
Before=gunicorn-dashboard.service

[Socket]
ListenStream=/run/gunicorn-dashboard.sock

[Install]
WantedBy=sockets.target
EOF

echo "✓ Gunicorn socket created at /etc/systemd/system/gunicorn-dashboard.socket"

# Create gunicorn service file
sudo tee /etc/systemd/system/gunicorn-dashboard.service > /dev/null << EOF
[Unit]
Description=Gunicorn application server for Sales Dashboard
Requires=gunicorn-dashboard.socket
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$DASHBOARD_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 4 \\
    --worker-class sync \\
    --bind unix:/run/gunicorn-dashboard.sock \\
    --error-logfile /var/log/gunicorn/dashboard-error.log \\
    --access-logfile /var/log/gunicorn/dashboard-access.log \\
    SalesDashboard.wsgi:application

ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Gunicorn service created at /etc/systemd/system/gunicorn-dashboard.service"

# Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown -R www-data:www-data /var/log/gunicorn
echo "✓ Log directory created"

echo ""
echo "[STEP 4] Creating Nginx configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create nginx config (adjust server_name to your domain)
sudo tee /etc/nginx/sites-available/dashboard > /dev/null << 'EOF'
upstream dashboard_server {
    server unix:/run/gunicorn-dashboard.sock fail_timeout=0;
}

server {
    listen 80;
    server_name 1capital.in www.1capital.in;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 1capital.in www.1capital.in;

    # SSL certificates (update path if different)
    ssl_certificate /etc/letsencrypt/live/1capital.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/1capital.in/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logs
    error_log /var/log/nginx/dashboard_error.log;
    access_log /var/log/nginx/dashboard_access.log;

    # Client upload size
    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /var/www/SalesDashboardProject/SalesDashboard/staticfiles/;
        expires 30d;
    }

    # Media files
    location /media/ {
        alias /var/www/SalesDashboardProject/SalesDashboard/media/;
        expires 7d;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://dashboard_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
EOF

echo "✓ Nginx configuration created"

# Enable the site
sudo ln -sf /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/dashboard 2>/dev/null || true
echo "✓ Nginx site enabled"

# Test nginx config
if sudo nginx -t; then
    echo "✓ Nginx configuration is valid"
else
    echo "✗ Nginx configuration has errors - please check manually"
    exit 1
fi

echo ""
echo "[STEP 5] Starting services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-dashboard.socket
sudo systemctl enable gunicorn-dashboard.service
sudo systemctl start gunicorn-dashboard.socket
sudo systemctl start gunicorn-dashboard.service

echo "✓ Gunicorn socket enabled and started"
echo "✓ Gunicorn service enabled and started"

# Reload nginx
sudo systemctl reload nginx
echo "✓ Nginx reloaded"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            PRODUCTION DEPLOYMENT COMPLETE ✅                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo "📊 Dashboard is now accessible at:"
echo "   https://1capital.in/dashboard/"
echo ""
echo "🔍 Check service status:"
echo "   sudo systemctl status gunicorn-dashboard"
echo ""
echo "📋 View logs:"
echo "   sudo journalctl -u gunicorn-dashboard -f"
echo "   sudo tail -f /var/log/nginx/dashboard_access.log"
echo ""
echo "🔄 To restart the service:"
echo "   sudo systemctl restart gunicorn-dashboard"
echo ""
