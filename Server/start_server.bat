@echo off
REM Startup script untuk Knight Game Server di Windows

echo Knight Multiplayer Game Server
echo ================================

:menu
echo.
echo Pilih konfigurasi server:
echo 1. Development Server (Thread model, single instance)
echo 2. Production Server (Thread pool, single instance)
echo 3. High Load Server (Thread pool, multiple instances)
echo 4. Maximum Performance (Process pool, multiple instances)
echo 5. Custom Configuration
echo 6. Test Server
echo 7. Exit
echo.

set /p choice="Masukkan pilihan (1-7): "

if "%choice%"=="1" goto dev_server
if "%choice%"=="2" goto prod_server
if "%choice%"=="3" goto high_load_server
if "%choice%"=="4" goto max_perf_server
if "%choice%"=="5" goto custom_config
if "%choice%"=="6" goto test_server
if "%choice%"=="7" goto exit
goto menu

:dev_server
echo Starting Development Server...
echo Configuration: Thread model, Port 8889
python server_thread_http.py --model thread --port 8889
goto menu

:prod_server
echo Starting Production Server...
echo Configuration: Thread pool, 20 workers, Port 8889
python server_thread_http.py --model pool --workers 20 --port 8889
goto menu

:high_load_server
echo Starting High Load Server...
echo Configuration: Thread pool, 3 instances, 25 workers each
echo Ports: 8889, 8890, 8891
python server_thread_http.py --model pool --servers 3 --workers 25 --port 8889
goto menu

:max_perf_server
echo Starting Maximum Performance Server...
echo Configuration: Process pool, 2 instances, 15 workers each
echo Ports: 8889, 8890
python server_thread_http.py --model process_pool --servers 2 --workers 15 --port 8889
goto menu

:custom_config
echo Custom Configuration
echo ====================
set /p model="Processing model (thread/process/pool/process_pool): "
set /p servers="Number of server instances (1-5): "
set /p workers="Workers per instance (5-50): "
set /p port="Starting port (8889): "

if "%model%"=="" set model=thread
if "%servers%"=="" set servers=1
if "%workers%"=="" set workers=10
if "%port%"=="" set port=8889

echo Starting Custom Server...
echo Configuration: %model% model, %servers% instances, %workers% workers, port %port%
python server_thread_http.py --model %model% --servers %servers% --workers %workers% --port %port%
goto menu

:test_server
echo Testing Server
echo ===============
set /p test_port="Server port to test (8889): "
if "%test_port%"=="" set test_port=8889

echo Running server tests on port %test_port%...
python test_server.py %test_port%
echo.
pause
goto menu

:exit
echo Goodbye!
pause
exit
