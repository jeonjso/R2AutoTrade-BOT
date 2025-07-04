# Jeon BOT

Bot trading R2 Testnet untuk memaksimalkan sinyal buy/sell token R2.

---

## ✨ Fitur

- Swap otomatis R2 ⇄ USDC
- Rotasi proxy otomatis per wallet
- Cek saldo token sebelum swap
- Log progres detail di console

---

## ⚙️ Cara Install & Jalankan

1. **Clone repository:**

git clone https://github.com/jeonjso/R2AutoTrade-BOT.git
cd R2AutoTrade-BOT

2. **Siapkan Python 3.8+**  
(bisa pakai Termux, Ubuntu, WSL, MacOS, atau VPS)

3. **Install dependencies:**

pip install web3 eth-account rich

4. **Buat file konfigurasi:**

- `pkevm.txt`  
  Daftar private keys (1 baris per key)

- `proxy.txt`  
  Daftar proxy  
  Contoh format:
  ```
  http://username:password@ip:port
  ```
  atau
  ```
  socks5://username:password@ip:port
  ```

- `token_abi.json`  
  ABI untuk kontrak token R2

- `router_swap_abi.json`  
  ABI untuk router swap

5. **Jalankan bot:**

python jeon.py

---

## 💻 Bisa Dijalan di:

- Termux Android
- Ubuntu Linux
- WSL (Windows Subsystem for Linux)
- MacOS Terminal
- VPS Linux

---

## ⚠️ Disclaimer

Gunakan script ini dengan tanggung jawab pribadi.
