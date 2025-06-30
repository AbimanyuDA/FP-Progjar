# Knightly Battle


### File utama:

1. player.py ==> enkapsulasi player. semua logika player ada disini
2. clientInterface.py ==> enkapsulasi segala request dari client.
3. main_multiplayer ==> program utama client.
4. http.py ==> enkapsulasi segala request dan response dari server.
5. server_thread_http.py ==> menjalankan server dengan mode thread.


### Protokol:

GET, POST

Lihat file `clientInterface.py` untuk contoh lebih lanjut.


### Cara menjalankan:

Install dependensi
```bash
pip install -r requirements.txt
```

Jalankan Server
```bash
python3 server_thread_http.py
```

Jalankan client
```bash
python3 main_multiplayer.py
```