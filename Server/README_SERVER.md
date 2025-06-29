# Knight Multiplayer Game Server

Server HTTP yang telah dimodifikasi untuk mendukung game multiplayer Knight dengan berbagai model task processing dan load balancer.

## Fitur Server

### 1. Game State Management
- Manajemen state pemain real-time
- Auto cleanup pemain yang tidak aktif (timeout 30 detik)
- Thread-safe operations dengan locking

### 2. Processing Models
Server mendukung 4 model pemrosesan:

#### Thread Model (Default)
```bash
python server_thread_http.py --model thread
```
- Setiap client ditangani oleh thread terpisah
- Cocok untuk game dengan pemain sedang (< 50 pemain)

#### Process Model
```bash
python server_thread_http.py --model process
```
- Mirip thread tapi menggunakan process terpisah
- Lebih isolasi, cocok untuk game yang membutuhkan stabilitas tinggi

#### Thread Pool Model
```bash
python server_thread_http.py --model pool --workers 20
```
- Menggunakan ThreadPoolExecutor dengan worker pool
- Lebih efisien untuk banyak koneksi pendek
- Cocok untuk game dengan banyak pemain (50-200 pemain)

#### Process Pool Model
```bash
python server_thread_http.py --model process_pool --workers 10
```
- Menggunakan ProcessPoolExecutor
- CPU intensive tasks, maksimal performa
- Cocok untuk game dengan komputasi berat

### 3. Load Balancer
Server dapat dijalankan dalam mode load balancer dengan multiple instances:

```bash
# Jalankan 3 server instances dengan load balancer
python server_thread_http.py --model pool --servers 3 --port 8889 --workers 15
```

Akan membuat:
- Server 1: localhost:8889
- Server 2: localhost:8890  
- Server 3: localhost:8891

Load balancer menggunakan round-robin algorithm dengan health checking.

## Game Commands

Server mendukung commands khusus untuk game:

### Get All Players
```
get_players
```
Response:
```json
{"status": "OK", "players": ["1", "2", "3"]}
```

### Get Player State
```
get_player_state <player_id>
```
Response:
```json
{
  "status": "OK",
  "state": {
    "x": 100,
    "y": 200,
    "facing_right": true,
    "is_attacking": false,
    "health": 6,
    "is_hit": false
  }
}
```

### Set Player State
```
set_player_state <player_id> {"x": 150, "y": 250, "health": 5}
```
Response:
```json
{"status": "OK", "message": "State updated"}
```

### Remove Player
```
remove_player <player_id>
```
Response:
```json
{"status": "OK", "message": "Player removed"}
```

## HTTP Endpoints

### Server Status
```
GET /status
```
Response:
```json
{
  "server": "Knight Game Server",
  "active_players": 3,
  "players": ["1", "2", "3"],
  "timestamp": "2025-06-29T10:30:00"
}
```

### Health Check
```
GET /health
```
Response: `Server is healthy`

### Game Homepage
```
GET /
```
Response: `Knight Multiplayer Game Server - Ready!`

## Menjalankan Server

### Basic Server (Single Instance)
```bash
python server_thread_http.py
```

### High Performance Setup
```bash
# Thread pool dengan 20 workers
python server_thread_http.py --model pool --workers 20

# Load balanced dengan 3 servers
python server_thread_http.py --model pool --servers 3 --workers 15
```

### Production Setup
```bash
# Process pool untuk stabilitas maksimal
python server_thread_http.py --model process_pool --servers 2 --workers 10 --port 8889
```

## Testing Server

### Test dengan curl
```bash
# Check server status
curl http://localhost:8889/status

# Health check
curl http://localhost:8889/health
```

### Test game commands dengan telnet
```bash
telnet localhost 8889
get_players
```

## Performance Tuning

### Untuk Game dengan Pemain Sedikit (< 20)
```bash
python server_thread_http.py --model thread
```

### Untuk Game dengan Pemain Sedang (20-100)
```bash
python server_thread_http.py --model pool --workers 25
```

### Untuk Game dengan Pemain Banyak (100+)
```bash
python server_thread_http.py --model pool --servers 3 --workers 30
```

## Logging

Server menggunakan logging level INFO. Untuk debugging, ubah level ke DEBUG di kode.

Log format: `%(asctime)s - %(levelname)s - %(message)s`

## Architecture

```
[Game Client] 
     ↓
[Load Balancer] → [Server Instance 1:8889]
     ↓         → [Server Instance 2:8890]  
     ↓         → [Server Instance 3:8891]
     ↓
[Shared Game State]
```

Setiap server instance memiliki HttpServer yang mengelola game state secara independen. Load balancer mendistribusikan koneksi secara round-robin.
