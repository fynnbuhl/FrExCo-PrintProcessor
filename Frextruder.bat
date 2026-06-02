@echo off
set "MAC=dc-a6-32-77-79-77"

echo Warte auf Verbindung des Raspberry Pi (MAC: %MAC%)...
echo Bitte stelle sicher, dass der mobile Hotspot (FREXCO-Hotspot) aktiviert ist.

:schleife
:: Durchsucht den ARP-Cache nach der MAC-Adresse
for /f "tokens=1" %%a in ('arp -a ^| findstr /i "%MAC%"') do (
    set "IP=%%a"
    goto :gefunden
)

:: Wartet 2 Sekunden vor dem nächsten Versuch, um die CPU zu schonen
timeout /t 2 >nul
goto :schleife

:gefunden
echo.
echo Raspberry Pi gefunden! 
echo IP-Adresse: %IP%
echo Starte Browser...

:: Oeffnet die URL im Standardbrowser
start http://%IP%:8080/webvisu.htm

echo Erledigt.
timeout /t 5 >nul
exit