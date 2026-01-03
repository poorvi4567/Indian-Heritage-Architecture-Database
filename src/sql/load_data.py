# src/sql/load_data.py

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

CSV_PATH = "data/processed/asi_master_dataset.csv"

def connect():
    return psycopg2.connect(
        dbname="heritage",
        user="postgres",
        password="yourpassword",
        host="localhost",
        port="5432"
    )

def insert_and_get_id(cur, table, field, value):
    """Insert a value into a table if not exists, return its ID."""
    if value is None or str(value).strip() == "":
        return None

    cur.execute(f"SELECT {table}_id FROM {table} WHERE {field} = %s", (value,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute(
        f"INSERT INTO {table} ({field}) VALUES (%s) RETURNING {table}_id",
        (value,)
    )
    return cur.fetchone()[0]


def load_data():
    df = pd.read_csv(CSV_PATH)

    conn = connect()
    cur = conn.cursor()

    for _, row in df.iterrows():

        # ---- LOCATION ----
        city = row.get("city")
        state = row.get("state")
        latitude = None
        longitude = None

        if pd.notna(row.get("coord")):
            try:
                coord = row["coord"].replace("Point(", "").replace(")", "")
                longitude, latitude = map(float, coord.split())
            except:
                pass

        # Check if location exists
        cur.execute(
            "SELECT location_id FROM location WHERE city=%s AND state=%s",
            (city, state)
        )
        loc_row = cur.fetchone()

        if loc_row:
            location_id = loc_row[0]
        else:
            cur.execute(
                "INSERT INTO location (city, state, latitude, longitude) "
                "VALUES (%s, %s, %s, %s) RETURNING location_id",
                (city, state, latitude, longitude)
            )
            location_id = cur.fetchone()[0]

        # ---- STYLE ----
        style = row.get("style")
        style_id = insert_and_get_id(cur, "architectural_style", "name", style)

        # ---- ARCHITECT ----
        architect = row.get("architect")
        architect_id = insert_and_get_id(cur, "architect", "name", architect)

        # ---- PERIOD (OPTIONAL) ----
        dynasty = row.get("dynasty") if "dynasty" in row else None
        period_id = None

        if dynasty:
            period_id = insert_and_get_id(cur, "period", "dynasty", dynasty)

        # ---- MONUMENT ----
        cur.execute("""
            INSERT INTO monument (monument_id, name, location_id, style_id, architect_id, period_id, coord, qid)
            VALUES (%s, %s, %s, %s, %s, %s, POINT(%s, %s), %s)
            ON CONFLICT (monument_id) DO NOTHING
        """, (
            row["monument_id"],
            row["asi_name"],
            location_id,
            style_id,
            architect_id,
            period_id,
            longitude,
            latitude,
            row.get("qid")
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("✔ CSV data loaded into SQL successfully.")


if __name__ == "__main__":
    load_data()
