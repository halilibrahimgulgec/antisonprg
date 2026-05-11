import sqlite3
from werkzeug.security import generate_password_hash
import os

DATABASE_PATH = 'kargo_data.db'

def setup_users_table():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Check if admin user exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin')
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                       ('admin', hashed_password, 'admin'))
        print("Admin kullanıcısı oluşturuldu (Kullanıcı: admin, Şifre: admin)")
    else:
        print("Admin kullanıcısı zaten mevcut.")
        
    conn.commit()
    conn.close()
    print("Kullanıcılar tablosu başarıyla hazırlandı.")

if __name__ == '__main__':
    setup_users_table()
