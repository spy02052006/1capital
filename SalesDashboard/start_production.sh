#!/bin/bash
# Production-Ready Dashboard Startup Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        SALES DASHBOARD - PRODUCTION STARTUP                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"

cd /var/www/SalesDashboardProject/SalesDashboard

echo ""
echo "Starting Django development server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Dashboard will be available at: http://localhost:8000/"
echo ""
echo "📱 Login Credentials:"
echo "   • Nitin Mude (Leader):  nitin_mude"
echo "   • Suhas Tare (Manager): suhas_tare"
echo "   • Harshal Ghatage (Manager): harshal_ghatage"
echo "   • Abhijeet Mane (Manager): abhijeet_mane"
echo "   • Any RM (converted to Manager): use lowercase name (e.g., avishek_kumar)"
echo ""
echo "   [All passwords are 'password' for demo purposes]"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver 0.0.0.0:8000
