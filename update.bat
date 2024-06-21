@echo off

taskkill /F /IM python.exe /T

gh repo sync

start /b run.bat

exit