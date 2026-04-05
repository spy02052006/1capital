#!/bin/bash
# Wrapper script to start gunicorn with PYTHONPATH set

export PYTHONPATH=/var/www/SalesDashboardProject
export DJANGO_SETTINGS_MODULE=SalesDashboard.settings

cd /var/www/SalesDashboardProject/SalesDashboard
/var/www/SalesDashboardProject/SalesDashboard/venv/bin/gunicorn --config gunicorn_config.py SalesDashboard.wsgi:application
