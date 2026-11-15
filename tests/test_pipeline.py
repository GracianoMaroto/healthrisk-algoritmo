"""
Suíte de Testes Automatizados de Homologação e Engenharia de Dados — Bloco 3.
Valida os 12 cenários críticos de arquitetura, integridade relacional, limpeza clínica,
escudo contra vazamento (Data Leakage Shield), imputação sem vazamento e performance preditiva.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from src.clean import recodificar_sentinelas
from src.features import FEATURES_MODELO_X, VARIAVEIS_BLOQUEADAS_VAZAMENTO
from src.train_models import StratifiedMedianImputer

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"


@pytest.fixture(scope="module")
def df_analytic() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "analytic.parquet")


@pytest.fixture(scope="module")
def df_territorial() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "territorial_uf.parquet")


@pytest.fixture(scope="module")
def metricas_modelos() -> dict:
    return json.loads((PROCESSED_DIR / "model_metrics.json").read_text(encoding="utf-8"))


def test_01_contratos_extracao_sha256():
    """CT-01: Verifica manifesto de extração, presença dos 16 XPTs do NHANES e hashes SHA-256."""
    manifest_path = RAW_DIR / "manifest_extracao.json"
    assert manifest_path.exists(), "Manifesto de extração ausente"
    manifesto = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "nhanes_2017_2018" in manifesto
    assert len(manifesto["nhanes_2017_2018"]) == 16
    for item in manifesto["nhanes_2017_2018"]:
        assert len(item["sha256_bruto"]) == 64
        assert item["n_linhas"] > 0
        assert item["n_seqn_unicos"] == item["n_linhas"]


def test_02_integridade_relacional_seqn_one_to_one(df_analytic: pd.DataFrame):
    """CT-02: Garante unicidade da chave id_participante (SEQN) e ausência de colunas duplicadas."""
    assert df_analytic["id_participante"].is_unique, "SEQN duplicado na base analítica"
    cols_sufixo = [c for c in df_analytic.columns if c.endswith("_x") or c.endswith("_y")]
    assert len(cols_sufixo) == 0, f"Colunas duplicadas de merge: {cols_sufixo}"
    assert len(df_analytic) == 5131


def test_03_universo_adulto_e_exclusao_gestantes(df_analytic: pd.DataFrame):
    """CT-03: Confirma filtro populacional (idade >= 18 anos e nenhuma gestante na amostra)."""
    assert (df_analytic["idade_anos"] >= 18).all(), "Encontrados menores de 18 anos na base analítica"
    if "RIDEXPRG" in df_analytic.columns:
        assert not (df_analytic["RIDEXPRG"] == 1).any(), "Gestantes não foram excluídas do alvo crônico"


def test_04_decodificacao_sentinelas_nhanes(df_analytic: pd.DataFrame):
    """CT-04: Verifica remoção de códigos 7/9/77/99/7777/9999 e preservação de 7 dias reais no PAQ."""
    s_teste = pd.Series([1, 2, 7, 9, 77, 99])
    limpa = recodificar_sentinelas(s_teste, {7, 9, 77, 99})
    assert limpa.isna().sum() == 4
    assert limpa.iloc[0] == 1 and limpa.iloc[1] == 2

    # Verifica que em escolaridade_ord só existem níveis 1 a 5 ou NaN (sem 7 ou 9)
    valores_esc = set(df_analytic["escolaridade_ord"].dropna().unique())
    assert valores_esc.issubset({1.0, 2.0, 3.0, 4.0, 5.0})

    # Verifica que o valor 7 (7 dias na semana) foi preservado em PAQ610/PAQ655
    assert (df_analytic["PAQ610"] == 7).any(), "Erro: 7 dias/semana foi apagado indevidamente como sentinela"
    assert not df_analytic["PAQ610"].isin([77, 99]).any()


def test_05_limites_clinicos_e_inconsistencias_logicas(df_analytic: pd.DataFrame):
    """CT-05: Valida que limites clínicos de antropometria, PA, sedentarismo e calorias foram respeitados."""
    assert df_analytic["altura_cm"].dropna().between(120, 210).all()
    assert df_analytic["peso_kg"].dropna().between(30, 250).all()
    assert df_analytic["cintura_cm"].dropna().between(50, 180).all()
    assert df_analytic["minutos_sentado"].dropna().between(0, 1440).all()
    assert df_analytic["energia_kcal"].dropna().between(500, 6000).all()
    assert df_analytic["acucar_g_dia"].dropna().between(0, 400).all()

    pa_ambas = df_analytic.dropna(subset=["pas_mmhg", "pad_mmhg"])
    assert (pa_ambas["pas_mmhg"] > pa_ambas["pad_mmhg"]).all()


def test_06_escudo_contra_vazamento_data_leakage_shield(df_analytic: pd.DataFrame):
    """CT-06: Garante isolamento total entre vetor preditor X e variáveis diagnósticas/glicêmicas."""
    assert len(FEATURES_MODELO_X) == 19
    intersecao = set(FEATURES_MODELO_X) & set(VARIAVEIS_BLOQUEADAS_VAZAMENTO)
    assert len(intersecao) == 0, f"Vazamento detectado no vetor X: {intersecao}"

    for col in FEATURES_MODELO_X:
        corr = abs(float(df_analytic[col].corr(df_analytic["diabetes"])))
        assert corr < 0.50, f"Correlação anormalmente alta ({corr:.3f}) em {col}: suspeita de vazamento"


def test_07_imputador_estratificado_sem_vazamento_treino_teste():
    """CT-07: Prova que valores extremos no conjunto de teste não contaminam as medianas de treino."""
    cols = ["idade_anos", "sexo", "hdl"]
    df_tr = pd.DataFrame({
        "idade_anos": [25, 26, 27, 65, 66, 67],
        "sexo": [1, 1, 1, 2, 2, 2],
        "hdl": [40.0, 42.0, 44.0, 50.0, 55.0, 60.0],
    })
    df_te = pd.DataFrame({
        "idade_anos": [25, 65],
        "sexo": [1, 2],
        "hdl": [np.nan, 9999.0],
    })
    imp = StratifiedMedianImputer(cols)
    imp.fit(df_tr)
    matriz_te = imp.transform(df_te)
    # Para homem 18-29 (linha 0 do teste), a mediana de treino deve ser exatos 42.0
    assert np.isclose(matriz_te[0, 2], 42.0)


def test_08_engenharia_features_tres_eixos(df_analytic: pd.DataFrame):
    """CT-08: Valida consistência matemática das variáveis derivadas nos 3 eixos."""
    # Razão cintura/estatura = cintura_cm / altura_cm
    dif_rce = (df_analytic["razao_cintura_estatura"] - (df_analytic["cintura_cm"] / df_analytic["altura_cm"])).abs().max()
    assert dif_rce < 1e-6

    # Cumpre OMS 150 min (600 MET-min/semana)
    sub_met = df_analytic.dropna(subset=["met_min_semana", "cumpre_oms_150"])
    esperado_oms = (sub_met["met_min_semana"] >= 600.0).astype(float)
    assert (sub_met["cumpre_oms_150"] == esperado_oms).all()


def test_09_isolamento_camada_territorial_uf(df_territorial: pd.DataFrame):
    """CT-09: Verifica se a base territorial brasileira contém as 27 UFs e o índice de contexto."""
    assert len(df_territorial) == 27
    assert df_territorial["uf"].nunique() == 27
    assert df_territorial["indice_contexto_territorial"].notna().all()
    assert "SEQN" not in df_territorial.columns and "id_participante" not in df_territorial.columns


def test_10_desempenho_modelos_e_prioridade_recall(metricas_modelos: dict):
    """CT-10: Verifica serialização dos 3 modelos, ROC-AUC >= 0.78 e Recall >= 80% no rastreio."""
    for arq in ["logistic_regression.joblib", "decision_tree.joblib", "random_forest.joblib"]:
        assert (MODELS_DIR / arq).exists(), f"Modelo serializado ausente: {arq}"
        mod = joblib.load(MODELS_DIR / arq)
        assert hasattr(mod, "predict_proba")

    for nome, m in metricas_modelos["modelos"].items():
        assert m["test_roc_auc"] >= 0.78, f"{nome} abaixo do ROC-AUC mínimo"
        assert m["limiar_rastreio"]["recall_sensibilidade"] >= 0.80, f"{nome} abaixo do Recall mínimo de triagem"
        assert m["limiar_rastreio"]["vpn"] >= 0.92, f"{nome} abaixo do VPN de segurança clínica"


def test_11_monotonia_faixas_risco_tercis(metricas_modelos: dict):
    """CT-11: Verifica crescimento estrito da prevalência real entre Baixo, Moderado e Alto Risco."""
    faixas = {f["faixa_risco"]: f["prevalencia_real_pct"] for f in metricas_modelos["validacao_faixas_risco_teste"]}
    assert faixas["Baixo Risco"] < 5.0
    assert faixas["Baixo Risco"] < faixas["Risco Moderado"] < faixas["Alto Risco"]
    assert faixas["Alto Risco"] > 40.0


def test_12_camada_sql_sqlite_integridade():
    """CT-12: Valida persistência e execução de consultas SQL no banco radar_diabetes.db."""
    db_path = PROCESSED_DIR / "radar_diabetes.db"
    assert db_path.exists()
    with sqlite3.connect(db_path) as conn:
        n_nhanes = conn.execute("SELECT COUNT(*) FROM fato_nhanes_analitico").fetchone()[0]
        n_uf = conn.execute("SELECT COUNT(*) FROM territorial_uf").fetchone()[0]
    assert n_nhanes == 5131
    assert n_uf == 27


def test_13_interface_streamlit_sem_excecoes():
    """CT-13: Executa o aplicativo Streamlit via AppTest e garante zero exceções nas 4 abas."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT_DIR / "app" / "app_radar_diabetes.py")).run(timeout=30)
    assert len(at.exception) == 0, f"Exceção detectada no Streamlit: {at.exception}"

