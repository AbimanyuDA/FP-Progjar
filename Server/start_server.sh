#!/bin/bash

# Startup script untuk Knight Game Server

echo "Knight Multiplayer Game Server"
echo "==============================="

show_menu() {
    echo
    echo "Pilih konfigurasi server:"
    echo "1. Development Server (Thread model, single instance)"
    echo "2. Production Server (Thread pool, single instance)"
    echo "3. High Load Server (Thread pool, multiple instances)"
    echo "4. Maximum Performance (Process pool, multiple instances)"
    echo "5. Custom Configuration"
    echo "6. Test Server"
    echo "7. Exit"
    echo
}

dev_server() {
    echo "Starting Development Server..."
    echo "Configuration: Thread model, Port 8889"
    python3 server_thread_http.py --model thread --port 8889
}

prod_server() {
    echo "Starting Production Server..."
    echo "Configuration: Thread pool, 20 workers, Port 8889"
    python3 server_thread_http.py --model pool --workers 20 --port 8889
}

high_load_server() {
    echo "Starting High Load Server..."
    echo "Configuration: Thread pool, 3 instances, 25 workers each"
    echo "Ports: 8889, 8890, 8891"
    python3 server_thread_http.py --model pool --servers 3 --workers 25 --port 8889
}

max_perf_server() {
    echo "Starting Maximum Performance Server..."
    echo "Configuration: Process pool, 2 instances, 15 workers each"
    echo "Ports: 8889, 8890"
    python3 server_thread_http.py --model process_pool --servers 2 --workers 15 --port 8889
}

custom_config() {
    echo "Custom Configuration"
    echo "===================="
    
    read -p "Processing model (thread/process/pool/process_pool) [thread]: " model
    read -p "Number of server instances (1-5) [1]: " servers
    read -p "Workers per instance (5-50) [10]: " workers
    read -p "Starting port [8889]: " port
    
    model=${model:-thread}
    servers=${servers:-1}
    workers=${workers:-10}
    port=${port:-8889}
    
    echo "Starting Custom Server..."
    echo "Configuration: $model model, $servers instances, $workers workers, port $port"
    python3 server_thread_http.py --model "$model" --servers "$servers" --workers "$workers" --port "$port"
}

test_server() {
    echo "Testing Server"
    echo "=============="
    read -p "Server port to test [8889]: " test_port
    test_port=${test_port:-8889}
    
    echo "Running server tests on port $test_port..."
    python3 test_server.py "$test_port"
    echo
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    read -p "Masukkan pilihan (1-7): " choice
    
    case $choice in
        1) dev_server ;;
        2) prod_server ;;
        3) high_load_server ;;
        4) max_perf_server ;;
        5) custom_config ;;
        6) test_server ;;
        7) echo "Goodbye!"; exit 0 ;;
        *) echo "Pilihan tidak valid. Silakan pilih 1-7." ;;
    esac
done
