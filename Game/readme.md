File utama:

1. player.py ==> enkapsulasi player. semua logika player ada disini
2. main_singleplayer ==> buat test game tanpa butuh server.
3. main_multiplayer ==> implementasinya mirip yang pac, dimana harus enter id pemain buat masuk dulu. karena belum ada server, belum pernah dicoba.

Yang harus diimplementasi di server:

```python
    def get_all_player_ids(self):
        command = "get_players"
        result = self.send_command(command)
        if result and result.get('status') == 'OK':
            return result.get('players', [])
        return []

    def get_player_state(self, player_id):
        command = f"get_player_state {player_id}"
        return self.send_command(command)

    def set_player_state(self, player_id, state):
        # Ubah state dict menjadi string JSON yang aman untuk URL
        state_json_string = json.dumps(state)
        command = f"set_player_state {player_id} {state_json_string}"
        self.send_command(command)
```

## Server Multiplayer (Updated)

HTTP server telah dimodifikasi untuk mendukung game multiplayer Knight dengan fitur:

### Fitur Server Baru:
- **Game State Management**: Mengelola state semua pemain secara real-time
- **Multiple Processing Models**: Thread, Process, Thread Pool, Process Pool
- **Load Balancer**: Mendistribusikan beban ke multiple server instances
- **Auto Cleanup**: Menghapus pemain yang tidak aktif otomatis
- **Health Monitoring**: Endpoint untuk monitoring kesehatan server

### Processing Models:
1. **Thread Model**: Setiap client ditangani thread terpisah (default)
2. **Process Model**: Menggunakan process terpisah untuk isolasi
3. **Pool Model**: ThreadPoolExecutor untuk efisiensi tinggi
4. **Process Pool**: ProcessPoolExecutor untuk performa maksimal

### Load Balancer:
Server bisa dijalankan dalam mode load balancer dengan multiple instances:
```bash
# 3 server instances dengan load balancer
python server_thread_http.py --model pool --servers 3 --port 8889
```

### Game Commands yang Didukung:
- `get_players` - Mendapat daftar semua pemain
- `get_player_state <id>` - Mendapat state pemain tertentu
- `set_player_state <id> <json_state>` - Set state pemain
- `remove_player <id>` - Hapus pemain dari game

### HTTP Endpoints:
- `GET /status` - Status server dan daftar pemain aktif
- `GET /health` - Health check server
- `GET /` - Homepage server

### Quick Start Server:
```bash
cd Server

# Windows
start_server.bat

# Linux/Mac  
chmod +x start_server.sh
./start_server.sh

# Manual
python server_thread_http.py --model pool --workers 20
```

### Testing:
```bash
# Test server functionality
python test_server.py

# Simulate multiple players
python simple_client.py multi 5 30

# Interactive client
python simple_client.py
```

## Bug Fixes

Fixed bugs in `main_multiplayer.py`:
- `SCREEN_WIDTH`/`SCREEN_HEIGHT` undefined variables → changed to `WIDTH`/`HEIGHT`
- Missing `all_players` parameter in `update()` method
- Server port changed from 55555 to 8889 for consistency

