import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from silver import BRONZE, limpiar

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

SQL_SILVER = """
INSERT INTO silver.lectura_5min
    (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
VALUES %s
ON CONFLICT (ts, dispositivo_id) DO UPDATE SET
    p_ac_kw = EXCLUDED.p_ac_kw,
    irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
    temp_modulo_c = EXCLUDED.temp_modulo_c
"""

SQL_FACT = """
INSERT INTO dwh.fact_energia_dia
    (fecha_key, dispositivo_key, energia_kwh, pct_datos_validos)
VALUES %s
ON CONFLICT (fecha_key, dispositivo_key) DO UPDATE SET
    energia_kwh = EXCLUDED.energia_kwh,
    pct_datos_validos = EXCLUDED.pct_datos_validos
"""


def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def resumen_diario(silver, bronze):
    """Gold: energía (potencia x 5/60 h) y % de datos válidos por día."""
    silver = silver.copy()
    silver["ts"] = pd.to_datetime(silver["ts"])
    silver["fecha"] = silver["ts"].dt.date
    silver["kwh"] = silver["p_ac_kw"] * 5 / 60

    bronze = bronze.copy()
    bronze["fecha"] = pd.to_datetime(bronze["ts"]).dt.date

    claves = ["fecha", "dispositivo_id"]
    gold = silver.groupby(claves).agg(
        energia_kwh=("kwh", "sum"), validas=("kwh", "size")
    )
    gold["leidas"] = bronze.groupby(claves).size()
    gold["pct"] = gold["validas"] / gold["leidas"] * 100
    return gold.reset_index()


def main():
    silver, rep = limpiar()
    bronze = pd.read_csv(BRONZE)
    silver["ts"] = pd.to_datetime(silver["ts"])
    gold = resumen_diario(silver, bronze)

    filas_silver = [
        (r.ts.to_pydatetime(), int(r.dispositivo_id), float(r.p_ac_kw),
         float(r.irradiancia_wm2), float(r.temp_modulo_c))
        for r in silver.itertuples()
    ]
    filas_gold = [
        (r.fecha, int(r.dispositivo_id), round(float(r.energia_kwh), 3),
         round(float(r.pct), 2))
        for r in gold.itertuples()
    ]

    conn = conectar()
    try:
        with conn, conn.cursor() as cur:
            execute_values(cur, SQL_SILVER, filas_silver)
            execute_values(cur, SQL_FACT, filas_gold)
            cur.execute("SELECT COUNT(*) FROM silver.lectura_5min")
            n_silver = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM dwh.fact_energia_dia")
            n_gold = cur.fetchone()[0]
    finally:
        conn.close()

    print("Reporte de limpieza Silver:", rep)
    print(f"silver.lectura_5min: {n_silver} filas")
    print(f"dwh.fact_energia_dia: {n_gold} filas")


if __name__ == "__main__":
    main()