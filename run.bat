@echo off
cd /d "E:\UNAIS KHAN\PROGRAMS\Finance With 4'Bs application"
set MYSQL_HOST=localhost
set MYSQL_USER=root
set MYSQL_PASSWORD=root
set MYSQL_DATABASE=finance_rates
set MYSQL_PORT=3306
python app.py
pause
