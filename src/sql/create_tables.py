# src/sql/create_tables.py
#this just creates the table, doesnt 
import psycopg2

def run_schema():
    conn = psycopg2.connect(
        dbname="heritage",
        user="postgres",
        password="yourpassword",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    with open("src/sql/schema.sql", "r", encoding="utf-8") as f:
        sql = f.read()

    cur.execute(sql)
    conn.commit()

    print("✔ Database tables created successfully.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    run_schema()
