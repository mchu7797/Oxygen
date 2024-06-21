@echo off

taskkill /F /IM python.exe /T

git pull

start /b run.bat

exit