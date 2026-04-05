import multiprocessing

# Gunicorn Configuration for Sales Dashboard
bind = "127.0.0.1:8001"  # Bind to localhost:8001, nginx will proxy
workers = 3  # Reduced from cpu_count to avoid memory issues
worker_class = "sync"
worker_connections = 100
timeout = 60
keepalive = 5
max_requests = 500
max_requests_jitter = 25

# Logging
accesslog = "/var/www/SalesDashboardProject/SalesDashboard/logs/gunicorn_access.log"
errorlog = "/var/www/SalesDashboardProject/SalesDashboard/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "salesdashboard"

# Environment
raw_env = [
    "DJANGO_SETTINGS_MODULE=SalesDashboard.settings",
    "DJANGO_DEBUG=False",
]
