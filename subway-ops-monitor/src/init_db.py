import psycopg2
import os
from config import Config

def init_db():
    if not Config.DATABASE_URL:
        print("[Error] DATABASE_URL is not set in .env. Cannot create table automatically.")
        print("Please add DATABASE_URL=postgresql://... to your .env file or run docs/schema.sql in Supabase Dashboard.")
        return False

    schema_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'schema.sql')
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()
        
        print("Dropping existing table...")
        cur.execute("DROP TABLE IF EXISTS subway_time CASCADE;")
        conn.commit()

        print("Executing schema.sql...")
        cur.execute(sql)
        conn.commit()
        
        cur.close()
        conn.close()
        print("Table 'subway_time' created successfully (or already exists).")
        return True
        
    except Exception as e:
        print(f"[Error] Failed to initialize DB: {e}")
        return False

if __name__ == "__main__":
    init_db()
