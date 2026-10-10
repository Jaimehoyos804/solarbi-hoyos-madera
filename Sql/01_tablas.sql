CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts               TIMESTAMP        NOT NULL,
    dispositivo_id   INTEGER          NOT NULL,
    p_ac_kw          NUMERIC(8,3)     NOT NULL,
    irradiancia_wm2  NUMERIC(8,1)     NOT NULL,
    temp_modulo_c    NUMERIC(5,1)     NOT NULL,
    PRIMARY KEY (ts, dispositivo_id)
);

CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha_key           DATE          NOT NULL,
    dispositivo_key     INTEGER       NOT NULL,
    energia_kwh         NUMERIC(10,3) NOT NULL,
    pct_datos_validos   NUMERIC(5,2)  NOT NULL,
    PRIMARY KEY (fecha_key, dispositivo_key)
);