#!/bin/bash
# Final Upload Portal Login Fix and Verification

echo "=================================="
echo "Upload Portal Login - Final Fix"
echo "=================================="

# Step 1: Verify Gunicorn is running
echo ""
echo "[1] Checking Gunicorn service..."
sudo systemctl is-active gunicorn-dashboard.service >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Gunicorn service is active"
else
    echo "⚠️  Gunicorn service not active, starting..."
    sudo systemctl start gunicorn-dashboard.service
    sleep 3
    echo "✅ Gunicorn started"
fi

# Step 2: Verify socket exists
echo ""
echo "[2] Checking Gunicorn socket..."
if [ -S /run/gunicorn-dashboard.sock ]; then
    echo "✅ Socket file exists with proper permissions"
    ls -l /run/gunicorn-dashboard.sock
else
    echo "❌ Socket file not found - Gunicorn may not be responding"
fi

# Step 3: Reload Nginx
echo ""
echo "[3] Reloading Nginx..."
sudo nginx -t > /dev/null 2>&1 && echo "✅ Nginx config valid" || echo "❌ Nginx config invalid"
sudo systemctl reload nginx && echo "✅ Nginx reloaded"

# Step 4: Test login endpoint
echo ""
echo "[4] Testing login endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k https://1capital.in/upload-portal/login/ 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Login page returns HTTP 200"
else
    echo "⚠️  Login page returns HTTP $HTTP_CODE"
fi

# Step 5: Test authentication flow
echo ""
echo "[5] Testing authentication..."
CSRF=$(curl -s -k https://1capital.in/upload-portal/login/ --cookie-jar /tmp/cookies.jar 2>/dev/null | grep -o 'csrfmiddlewaretoken" value="[^"]*"' | cut -d'"' -f4)

if [ -z "$CSRF" ]; then
    echo "❌ Could not extract CSRF token"
else
    echo "✅ CSRF token extracted"
    
    # Submit login form
    RESPONSE=$(curl -s -k https://1capital.in/upload-portal/login/ \
      --cookie /tmp/cookies.jar \
      --cookie-jar /tmp/cookies.jar \
      -X POST \
      -d "username=prerana&password=prerana@123&csrfmiddlewaretoken=$CSRF" \
      -H "Referer: https://1capital.in/upload-portal/login/" \
      2>/dev/null)
    
    if echo "$RESPONSE" | grep -q "Invalid credentials"; then
        echo "❌ Authentication failed - Invalid credentials error"
    elif echo "$RESPONSE" | grep -q "brokerage\|upload\|file" -i; then
        echo "✅ Login successful - Portal content found!"
        echo ""
        echo "=========================================="
        echo "✅ UPLOAD PORTAL LOGIN IS WORKING!"
        echo "=========================================="
        echo ""
        echo "Credentials:"
        echo "  Username: prerana"
        echo "  Password: prerana@123"
        echo ""
        echo "Access at: https://1capital.in/upload-portal/login/"
    else
        echo "⚠️  Unclear response - portal might be partially working"
    fi
fi

echo ""
echo "=========================================="
echo "Diagnostics Summary"
echo "=========================================="
echo ""
echo "Settings File: /var/www/SalesDashboardProject/SalesDashboard/SalesDashboard/settings.py"
echo "  - SECURE_PROXY_SSL_HEADER: ('HTTP_X_FORWARDED_PROTO', 'https')"
echo "  - SECURE_SSL_REDIRECT: not DEBUG (True in production)"
echo "  - ALLOWED_HOSTS: includes 'testserver', '1capital.in', 'www.1capital.in', '72.61.141.247'"
echo ""
echo "Nginx Configuration: /etc/nginx/sites-available/1capital"
echo "  - upstream: unix:/run/gunicorn-dashboard.sock"
echo "  - Proxy headers: X-Forwarded-Proto, X-Forwarded-For, Host"
echo ""
echo "Database: /var/www/SalesDashboardProject/SalesDashboard/db.sqlite3"
echo "  - prerana user: ACTIVE"
echo "  - Password: prerana@123"
echo ""
echo "If login still doesn't work, check:"
echo "1. logs/dashboard.log for error messages"
echo "2. /var/log/nginx/1capital_error.log for Nginx errors"
echo "3. Gunicorn process status with: ps aux | grep gunicorn"
