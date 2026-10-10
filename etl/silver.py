
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRONZE = RAIZ / "data" / "bronze" / "telemetria.csv"
SILVER = RAIZ / "data" / "silver" / "lectura_5min.csv"

P_MIN_KW = 0.0
P_MAX_KW = 5.0


def limpiar():
    df = pd.read_csv(BRONZE)
    lectura = len(df)

    # Eliminar duplicados
    df = df.drop_duplicates()
    rechazados_duplicados = lectura - len(df)

    # Eliminar datos faltantes
    antes = len(df)
    df = df.dropna()
    rechazados_faltantes = antes - len(df)

    # Validar el rango físico de la potencia
    antes = len(df)
    df = df[
        (df["p_ac_kw"] >= P_MIN_KW)
        & (df["p_ac_kw"] <= P_MAX_KW)
    ]
    rechazados_rango = antes - len(df)

    # Calcular registros válidos
    validas = len(df)

    reporte = {
        "leidas": lectura,
        "rech_duplicados": rechazados_duplicados,
        "rech_faltantes": rechazados_faltantes,
        "rech_rango": rechazados_rango,
        "validas": validas,
        "pct_validas": round(validas / lectura * 100, 2)
        if lectura > 0 else 0,
    }

    # Guardar archivo Silver
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER, index=False)

    return df, reporte


if __name__ == "__main__":
    df, reporte = limpiar()

    print("Reporte de limpieza Silver")
    for clave, valor in reporte.items():
        print(f"{clave}: {valor}")
