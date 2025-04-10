import urllib.parse

# Конфигурация подключения к базе данных с использованием Windows аутентификации
params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-E63O6PHD;DATABASE=Library;Trusted_Connection=yes;")
SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=%s" % params
