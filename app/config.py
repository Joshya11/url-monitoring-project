import os

MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'monitor')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'monitorpass')
MYSQL_DB = os.getenv('MYSQL_DB', 'monitor')

PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
