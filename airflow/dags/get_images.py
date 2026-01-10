from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine
from datetime import datetime
import requests
import pandas as pd


# ======================
# DAG definition
# ======================
dag = DAG(
    dag_id="get_images",
    description="Obter catálogo de imagens do INPE",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["inpe", "images"],
)


# ======================
# Helper function
# ======================
def insert_param(link: str) -> str:
    return f"{link}?email=bruno.aqnrocha@gmail.com"


# ======================
# Main task
# ======================

def get_images():
    base_url = "http://www.dgi.inpe.br/lgi-stac/collections/CBERS4A_WPM_L4_DN/items"

    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    for page in range(1, 600):
        # fetch JSON
        response = requests.get(base_url, params={"page": page, "limit": 1000}, timeout=60)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])
        if not features:
            break

        records = []
        for item in features:
            records.append((
                item["id"],
                item["collection"],
                str(item["geometry"]["coordinates"][0]),
                item["properties"]["datetime"],
                item["properties"]["satellite"],
                item["properties"].get("cloud_cover", 0),
                insert_param(item["assets"]["pan"]["href"]),
                insert_param(item["assets"]["blue"]["href"]),
                insert_param(item["assets"]["green"]["href"]),
                insert_param(item["assets"]["red"]["href"]),
                insert_param(item["assets"]["nir"]["href"]),
                item["assets"]["thumbnail"]["href"],
            ))

        insert_query = """
            INSERT INTO images (
                id, colecao, coordenadas, data, satelite, cloud_cover,
                banda_pan, banda_azul, banda_verde, banda_vermelho, banda_nir, thumbnail
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        cursor.executemany(insert_query, records)
        conn.commit()

    cursor.close()
    conn.close()


# ======================
# Operator
# ======================
get_images_task = PythonOperator(
    task_id="get_images",
    python_callable=get_images,
    dag=dag,
)
