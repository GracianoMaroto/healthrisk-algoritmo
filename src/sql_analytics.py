"""
Camada Analítica SQL (SQLite) para consolidação de indicadores gerenciais e territoriais.
Materializa as consultas SQL planejadas no Bloco 2 (Seções 2.3, 2.5 e 4.7) em um banco
relacional local (data/processed/radar_diabetes.db) e exporta relatórios agregados.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
TABLES_DIR = ROOT_DIR / "reports" / "tables"
DB_PATH = PROCESSED_DIR / "radar_diabetes.db"


CONSULTAS_SQL: dict[str, str] = {
    "sql1_estratificacao_faixa_etaria_sexo": """
        SELECT
            faixa_etaria,
            CASE WHEN sexo = 1 THEN 'Masculino' ELSE 'Feminino' END AS sexo_desc,
            COUNT(*) AS n_participantes,
            ROUND(AVG(diabetes) * 100.0, 2) AS prevalencia_real_pct,
            ROUND(AVG(prob_risco_rf) * 100.0, 2) AS prob_media_rf_pct,
            ROUND(AVG(razao_cintura_estatura), 3) AS media_rce,
            ROUND(AVG(met_min_semana), 1) AS media_met_sem
        FROM fato_nhanes_analitico
        GROUP BY faixa_etaria, sexo
        ORDER BY faixa_etaria, sexo;
    """,
    "sql2_perfis_comportamentais_dieta_movimento": """
        SELECT
            perfil_movimento,
            CASE
                WHEN indice_qualidade_dieta >= 0.25 THEN '1. Dieta Protetora (Top)'
                WHEN indice_qualidade_dieta <= -0.25 THEN '3. Dieta Hipercalórica/Sódio'
                ELSE '2. Dieta Intermediária'
            END AS perfil_dieta,
            COUNT(*) AS n_individuos,
            ROUND(AVG(diabetes) * 100.0, 2) AS prevalencia_diabetes_pct,
            ROUND(AVG(prob_risco_rf) * 100.0, 2) AS risco_predito_medio_pct,
            ROUND(AVG(imc), 2) AS imc_medio
        FROM fato_nhanes_analitico
        WHERE perfil_movimento != 'Desconhecido' AND indice_qualidade_dieta IS NOT NULL
        GROUP BY perfil_movimento, perfil_dieta
        ORDER BY prevalencia_diabetes_pct DESC;
    """,
    "sql3_territorio_datasus_ibge_uf": """
        SELECT
            d.uf,
            i.nome_uf,
            i.regiao,
            d.ano,
            ROUND(SUM(d.internacoes_diabetes) * 100000.0 / i.populacao, 2) AS internacoes_100k,
            d.n_estabelecimentos_ab,
            d.cobertura_ab,
            i.renda_mediana_uf,
            i.prev_diabetes_uf,
            i.pct_insuf_atividade_uf,
            t.indice_contexto_territorial,
            t.prioridade_territorial
        FROM fato_datasus d
        JOIN dim_ibge_uf i ON i.uf = d.uf
        JOIN territorial_uf t ON t.uf = d.uf
        GROUP BY d.uf, d.ano
        ORDER BY t.indice_contexto_territorial DESC;
    """,
    "sql4_gradiente_socioeconomico_inseguranca": """
        SELECT
            CASE
                WHEN razao_renda_pobreza < 1.30 THEN '1. Baixa Renda (PIR < 1.3)'
                WHEN razao_renda_pobreza < 3.50 THEN '2. Renda Média (1.3 <= PIR < 3.5)'
                ELSE '3. Alta Renda (PIR >= 3.5)'
            END AS estrato_renda,
            CASE WHEN inseguranca_alimentar = 1 THEN 'Com Insegurança Alimentar' ELSE 'Segurança Plena' END AS status_seguranca_alimentar,
            COUNT(*) AS n_amostra,
            ROUND(AVG(diabetes) * 100.0, 2) AS prevalencia_diabetes_pct,
            ROUND(AVG(prob_risco_rf) * 100.0, 2) AS risco_medio_modelo_pct
        FROM fato_nhanes_analitico
        WHERE razao_renda_pobreza IS NOT NULL AND inseguranca_alimentar IS NOT NULL
        GROUP BY estrato_renda, status_seguranca_alimentar
        ORDER BY estrato_renda, status_seguranca_alimentar;
    """,
}


def executar_camada_sql() -> dict[str, pd.DataFrame]:
    """
    Carrega os datasets processados em um banco SQLite local, executa as consultas
    analíticas planejadas no Bloco 2 e exporta os resultados em CSV.
    """
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df_analytic = pd.read_parquet(PROCESSED_DIR / "analytic.parquet")
    df_terr = pd.read_parquet(PROCESSED_DIR / "territorial_uf.parquet")
    df_ibge = pd.read_parquet(ROOT_DIR / "data" / "raw" / "ibge" / "ibge_uf_indicadores.parquet")
    df_datasus = pd.read_csv(ROOT_DIR / "data" / "raw" / "datasus" / "datasus_sih_cnes_uf.csv")

    if DB_PATH.exists():
        DB_PATH.unlink()

    resultados_sql: dict[str, pd.DataFrame] = {}
    with sqlite3.connect(DB_PATH) as conn:
        df_analytic.to_sql("fato_nhanes_analitico", conn, index=False, if_exists="replace")
        df_terr.to_sql("territorial_uf", conn, index=False, if_exists="replace")
        df_ibge.to_sql("dim_ibge_uf", conn, index=False, if_exists="replace")
        df_datasus.to_sql("fato_datasus", conn, index=False, if_exists="replace")

        for nome_q, sql in CONSULTAS_SQL.items():
            df_res = pd.read_sql_query(sql, conn)
            df_res.to_csv(TABLES_DIR / f"{nome_q}.csv", index=False, encoding="utf-8")
            resultados_sql[nome_q] = df_res
            print(f"[SQL] {nome_q} executada ({len(df_res)} linhas retornadas)")

    return resultados_sql


if __name__ == "__main__":
    executar_camada_sql()
