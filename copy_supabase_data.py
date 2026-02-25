"""
Supabase'den SQLite'a veri kopyalama (MCP ile)
Bu scripti manuel çalıştırın, veriler terminale yazılacak
"""
import sqlite3

# Manuel olarak Supabase'den alacağınız verileri buraya yapıştırın
# Şu komutları çalıştırın:

instructions = """
1. Supabase MCP ile şu komutları çalıştırın:

   mcp__supabase__execute_sql: SELECT * FROM yakit
   mcp__supabase__execute_sql: SELECT * FROM agirlik
   mcp__supabase__execute_sql: SELECT * FROM arac_takip

2. Çıkan JSON verilerini not alın

3. Bu scripti çalıştırıp verileri SQLite'a aktarın
"""

print(instructions)
