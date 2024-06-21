@echo off

taskkill /F /IM python.exe /T

gh repo sync

start run.bat

exit