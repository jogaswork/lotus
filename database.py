import sqlite3
import json
from contextlib import closing
import config

DB_PATH = "shop.db"

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'новый',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                delivery_method TEXT
            )
        """)
            
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                referrer_id INTEGER,
                referral_earned REAL NOT NULL DEFAULT 0,
                is_worker INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0
            )
        """)
        cur.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cur.fetchall()]
        if "is_worker" not in columns: cur.execute("ALTER TABLE users ADD COLUMN is_worker INTEGER DEFAULT 0")
        if "is_banned" not in columns: cur.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        if "is_admin" not in columns: cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            
        cur.execute("""
            CREATE TABLE IF NOT EXISTS topups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                amount REAL NOT NULL,
                screenshot_file_id TEXT,
                status TEXT DEFAULT 'ожидает',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS worker_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER NOT NULL,
                city TEXT,
                district TEXT,
                product TEXT,
                type TEXT,
                package_size INTEGER,
                quantity INTEGER,
                price REAL,
                status TEXT DEFAULT 'Свободен',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        cur.execute("PRAGMA table_info(worker_orders)")
        w_columns = [row[1] for row in cur.fetchall()]
        if "package_size" not in w_columns: cur.execute("ALTER TABLE worker_orders ADD COLUMN package_size INTEGER DEFAULT 1")
        if "price" not in w_columns: cur.execute("ALTER TABLE worker_orders ADD COLUMN price REAL DEFAULT 0")
        if "status" not in w_columns: cur.execute("ALTER TABLE worker_orders ADD COLUMN status TEXT DEFAULT 'Свободен'")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS custom_cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_name TEXT NOT NULL,
                district_name TEXT NOT NULL
            )
        """)
        
        cur.execute("SELECT COUNT(*) FROM custom_cities")
        if cur.fetchone()[0] == 0:
            for c_name, dists in config.CITIES:
                for d in dists:
                    cur.execute("INSERT INTO custom_cities (city_name, district_name) VALUES (?, ?)", (c_name, d))

        cur.execute("""
            CREATE TABLE IF NOT EXISTS warehouse (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT DEFAULT 'Описание отсутствует',
                base_price REAL,
                prices TEXT DEFAULT '{}',
                unit TEXT DEFAULT 'г',
                is_active INTEGER DEFAULT 1,
                emoji TEXT DEFAULT '📦'
            )
        """)
        
        cur.execute("PRAGMA table_info(warehouse)")
        w_cols = [row[1] for row in cur.fetchall()]
        if "prices" not in w_cols: 
            cur.execute("ALTER TABLE warehouse ADD COLUMN prices TEXT DEFAULT '{}'")

        cur.execute("SELECT COUNT(*) FROM warehouse")
        if cur.fetchone()[0] == 0:
            for i in range(1, 26):
                cur.execute("INSERT INTO warehouse (id, name, base_price, prices) VALUES (?, ?, ?, ?)", (i, f"Слот {i}", 0.0, '{}'))

        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)

        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('chat_link', 'https://t.me/LotusssMarket_bot_Shop')")
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card_number', '0000 0000 0000 0000')")
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card_holder', 'Имя Фамилия Банк')")
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('operator_username', '@LotusssMarket_bot_Shop')")
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('operator_status', 'online')")
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('operator_eta', '5 мин')")
        
        cur.execute("UPDATE settings SET value = 'https://t.me/LotusssMarket_bot_Shop' WHERE key = 'chat_link' AND value NOT LIKE 'http%'")
        cur.execute("UPDATE settings SET value = '@LotusssMarket_bot_Shop' WHERE key = 'operator_username' AND value NOT LIKE '@%'")
        
        cur.execute("DELETE FROM worker_orders WHERE city = 'all' OR district = 'all'")
        
        conn.commit()

# --- ЛОГИРОВАНИЕ ДЕЙСТВИЙ ---
def log_action(user_id: int, username: str, action: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO action_logs (user_id, username, action) VALUES (?, ?, ?)", (user_id, username, action))
        conn.commit()

def count_action_logs() -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM action_logs")
        return cur.fetchone()[0]

def get_action_logs(limit: int = 10, offset: int = 0) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, action, created_at FROM action_logs ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        return cur.fetchall()

def get_setting(key: str, default: str = "") -> str:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default

def set_setting(key: str, value: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def get_user_orders(user_id: int) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, product_name, price, status, created_at, delivery_method FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return cur.fetchall()

def get_all_orders(limit: int = 50) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, username, product_name, price, status, created_at, delivery_method FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

def get_all_topups(limit: int = 20) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, amount, status, created_at FROM topups ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

def count_all_users() -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

def get_or_create_user(user_id: int, username: str | None) -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, 0)", (user_id, username))
            conn.commit()
            return 0.0
        else:
            cur.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
            conn.commit()
            return row[0]

def get_balance(user_id: int) -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0.0

def get_user_profile(user_id: int) -> tuple | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, balance, created_at FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()

def count_user_orders(user_id: int) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
        return cur.fetchone()[0]

def user_exists(user_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone() is not None

def get_user_by_username(username: str) -> tuple | None:
    clean_username = username.lstrip('@')
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, is_banned, is_worker FROM users WHERE username = ? COLLATE NOCASE", (clean_username,))
        return cur.fetchone()

def set_referrer(user_id: int, referrer_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL", (referrer_id, user_id))
        conn.commit()

def get_referrer(user_id: int) -> int | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else None

def get_referral_earned(user_id: int) -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT referral_earned FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0.0

def get_referrals(user_id: int) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, created_at FROM users WHERE referrer_id = ?", (user_id,))
        return cur.fetchall()

def add_referral_earning(referrer_id: int, amount: float) -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + ?, referral_earned = referral_earned + ? WHERE user_id = ?", (amount, amount, referrer_id))
        conn.commit()
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (referrer_id,))
        return cur.fetchone()[0]

def change_balance(user_id: int, delta: float) -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (delta, user_id))
        conn.commit()
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()[0]

def create_topup(user_id: int, username: str | None, amount: float, screenshot_file_id: str) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO topups (user_id, username, amount, screenshot_file_id) VALUES (?, ?, ?, ?)", (user_id, username, amount, screenshot_file_id))
        conn.commit()
        return cur.lastrowid

def get_topup(topup_id: int) -> tuple | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, username, amount, screenshot_file_id, status FROM topups WHERE id = ?", (topup_id,))
        return cur.fetchone()

def set_topup_status(topup_id: int, status: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE topups SET status = ? WHERE id = ?", (status, topup_id))
        conn.commit()

def is_banned(user_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return bool(row[0]) if row else False

def is_worker(user_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_worker FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return bool(row[0]) if row else False

def is_admin_user(user_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return bool(row[0]) if row else False

def set_user_banned(user_id: int, status: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (status, user_id))
        conn.commit()

def set_user_worker(user_id: int, status: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_worker = ? WHERE user_id = ?", (status, user_id))
        conn.commit()

def set_user_admin(user_id: int, status: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (status, user_id))
        conn.commit()

def get_banned_users() -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE is_banned = 1")
        return cur.fetchall()

def get_workers() -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE is_worker = 1")
        return cur.fetchall()

def get_admins() -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE is_admin = 1")
        return cur.fetchall()

def get_all_warehouse_items() -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, base_price, unit, is_active, emoji FROM warehouse ORDER BY id")
        return cur.fetchall()

def get_active_warehouse_items() -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, base_price, unit, is_active, emoji FROM warehouse WHERE is_active = 1 AND base_price > 0 ORDER BY id")
        return cur.fetchall()

def get_warehouse_item(item_id: int) -> tuple | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, base_price, unit, is_active, emoji, prices FROM warehouse WHERE id = ?", (item_id,))
        return cur.fetchone()

def update_warehouse_field(item_id: int, field: str, value):
    allowed_fields = ["name", "description", "base_price", "unit", "is_active", "emoji", "prices"]
    if field not in allowed_fields: return
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE warehouse SET {field} = ? WHERE id = ?", (value, item_id))
        conn.commit()

def update_warehouse_price(item_id: int, unit_qty: int, price: float):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT prices, base_price FROM warehouse WHERE id = ?", (item_id,))
        row = cur.fetchone()
        if not row: return
        
        prices_json, base_price = row
        prices = json.loads(prices_json) if prices_json else {}
        prices[str(unit_qty)] = price
        new_prices_json = json.dumps(prices)
        
        if unit_qty == 1 or base_price == 0:
            cur.execute("UPDATE warehouse SET prices = ?, base_price = ? WHERE id = ?", (new_prices_json, price, item_id))
        else:
            cur.execute("UPDATE warehouse SET prices = ? WHERE id = ?", (new_prices_json, item_id))
        conn.commit()

def count_stashes_for_product(product_name: str) -> tuple[int, int]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM worker_orders WHERE product = ? AND status = 'Свободен'", (product_name,))
        free = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM worker_orders WHERE product = ? AND status = 'Продан'", (product_name,))
        sold = cur.fetchone()[0]
        return free, sold

def get_all_custom_cities() -> dict[str, list[str]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT city_name, district_name FROM custom_cities")
        rows = cur.fetchall()
        cities = {}
        for city, district in rows:
            if city not in cities: cities[city] = []
            cities[city].append(district)
        return cities

def add_custom_city(city_name: str, district_name: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO custom_cities (city_name, district_name) VALUES (?, ?)", (city_name, district_name))
        conn.commit()

def delete_custom_city(city_name: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM custom_cities WHERE city_name = ?", (city_name,))
        conn.commit()

def add_worker_order(worker_id: int, city: str, district: str, product: str, type_val: str, package_size: int, quantity: int, price: float):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        for _ in range(quantity):
            cur.execute(
                "INSERT INTO worker_orders (worker_id, city, district, product, type, package_size, quantity, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (worker_id, city, district, product, type_val, package_size, 1, price)
            )
        conn.commit()

def get_active_worker_stashes(worker_id: int) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, product, package_size, type FROM worker_orders WHERE worker_id = ? AND status = 'Свободен' ORDER BY id DESC", (worker_id,))
        return cur.fetchall()

def delete_worker_stash(stash_id: int, worker_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM worker_orders WHERE id = ? AND worker_id = ? AND status = 'Свободен'", (stash_id, worker_id))
        conn.commit()
        return cur.rowcount > 0

def delete_all_worker_stashes(worker_id: int) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM worker_orders WHERE worker_id = ? AND status = 'Свободен'", (worker_id,))
        deleted_count = cur.rowcount
        conn.commit()
        return deleted_count

def get_worker_stats(worker_id: int) -> tuple[int, int, int]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM worker_orders WHERE worker_id = ?", (worker_id,))
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM worker_orders WHERE worker_id = ? AND status = 'Продан'", (worker_id,))
        sold = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM worker_orders WHERE worker_id = ? AND status = 'Свободен'", (worker_id,))
        free = cur.fetchone()[0]
        return total, sold, free

def boost_worker_stats(worker_id: int, amount: int = 1000):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        for _ in range(amount):
            cur.execute(
                "INSERT INTO worker_orders (worker_id, city, district, product, type, package_size, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (worker_id, "Накрутка", "Накрутка", "Накрутка", "Накрутка", 1, 1, 0, 'Продан')
            )
        conn.commit()

def get_available_cities() -> list[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT city FROM worker_orders WHERE status = 'Свободен' AND city != 'all'")
        return [r[0] for r in cur.fetchall()]

def get_available_districts(city: str) -> list[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT district FROM worker_orders WHERE status = 'Свободен' AND city = ? AND district != 'all'", (city,))
        return [r[0] for r in cur.fetchall()]

def get_available_products_with_emojis(city: str, district: str) -> list[tuple[str, str]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT wo.product, COALESCE(w.emoji, '📦') 
            FROM worker_orders wo
            LEFT JOIN warehouse w ON wo.product = w.name
            WHERE wo.status = 'Свободен' AND wo.city = ? AND wo.district = ?
        """, (city, district))
        return cur.fetchall()

def get_available_types(city: str, district: str, product: str) -> list[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT type FROM worker_orders WHERE status = 'Свободен' AND city = ? AND district = ? AND product = ?", (city, district, product))
        return [r[0] for r in cur.fetchall()]

def get_available_sizes_prices(city: str, district: str, product: str, type_val: str) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT package_size, price, COUNT(id) 
            FROM worker_orders 
            WHERE status = 'Свободен' AND city = ? AND district = ? AND product = ? AND type = ? 
            GROUP BY package_size, price
        """, (city, district, product, type_val))
        return cur.fetchall()

def reserve_and_buy_stash(user_id: int, username: str, city: str, district: str, product: str, type_val: str, size: int) -> tuple[bool, str | int, float]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cur.fetchone()[0]
        
        cur.execute("SELECT id, price FROM worker_orders WHERE status = 'Свободен' AND city = ? AND district = ? AND product = ? AND type = ? AND package_size = ? LIMIT 1", (city, district, product, type_val, size))
        stash = cur.fetchone()
        
        if not stash: return False, "Этот клад только что купили.", 0.0
        stash_id, price = stash
        
        if balance < price: return False, f"Недостаточно средств. Нужно {price} ₽", price
        
        cur.execute("UPDATE worker_orders SET status = 'Продан' WHERE id = ?", (stash_id,))
        cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
        
        order_name = f"{product} | {type_val} | {size} шт"
        cur.execute("INSERT INTO orders (user_id, username, product_id, product_name, price, delivery_method) VALUES (?, ?, ?, ?, ?, ?)", (user_id, username, stash_id, order_name, price, type_val))
        order_id = cur.lastrowid
        
        conn.commit()
        return True, order_id, price