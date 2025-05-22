# init_db.py
import sqlite3

conn = sqlite3.connect("energy_ocpp.db")  # ← 確保這個檔案位於執行目錄中
cursor = conn.cursor()

# 建立 transactions 資料表（已存在會跳過）
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cp_id TEXT,
    transaction_id INTEGER,
    id_tag TEXT,
    start_time TEXT,
    stop_time TEXT,
    meter_start INTEGER,
    meter_stop INTEGER
)
""")

# 建立 boot_notifications 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS boot_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cp_id TEXT NOT NULL,
    model TEXT,
    vendor TEXT,
    serial_number TEXT,
    firmware_version TEXT,
    boot_time TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print("✅ 已建立 transactions 與 boot_notifications 資料表（如果不存在）")
