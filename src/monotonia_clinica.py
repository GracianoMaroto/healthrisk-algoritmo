"""
Escudo de monotonia clínica para o simulador individual.

O NHANES é transversal: 75,8% dos diabéticos já tinham diagnóstico e já haviam
mudado dieta/rotina. Por isso a LR/RF observacionais aprendem sinais invertidos
em hábitos acionáveis (mais fibra → mais risco; exercício no RF → mais risco).

Na inferência da pessoa (Streamlit, app mobile, 6 perguntas direcionadas) os
coeficientes acionáveis são forçados ao sentido clínico (OMS/FINDRISC) e o
intercepto é recalibrado para preservar a probabilidade média de treino.
Os .joblib originais e as métricas acadêmicas permanecem intactos.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.features import FEATURES_MODELO_X

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
RANDOM_STATE = 42

# +1: quanto maior o valor, maior o risco. -1: fator protetor.
# sexo, escolaridade e renda ficam livres (sem consenso clínico unívoco).
SINAIS_CLINICOS: dict[str, int] = {
    "idade_anos": 1,
    "inseguranca_alimentar": 1,
    "densidade_acucar": 1,
    "densidade_fibra": -1,
    "excesso_sodio": 1,
    "indice_qualidade_dieta": -1,
    "refeicao_pronta": 1,
    "met_min_semana": -1,
    "cumpre_oms_150": -1,
    "minutos_sentado": 1,
    "sedentarismo_alto": 1,
    "imc": 1,
    "razao_cintura_estatura": 1,
    "pressao_alta": 1,
    "hdl": -1,
    "historico_familiar_diabetes": 1,
}


def carregar_treino_referencia() -> tuple[pd.DataFrame, pd.Series]:
    """Recria o corte 80/20 estratificado usado em src/train_models.py."""
    df = pd.read_parquet(PROCESSED_DIR / "analytic.parquet")
    indices_treino, _ = train_test_split(
        df.index,
        test_size=0.20,
        stratify=df["diabetes"],
        random_state=RANDOM_STATE,
    )
    X = df.loc[indices_treino, FEATURES_MODELO_X].copy()
    y = df.loc[indices_treino, "diabetes"].copy()
    return X, y


def aplicar_monotonia_clinica(
    pipeline: Pipeline,
    X_ref: pd.DataFrame | None = None,
    y_ref: pd.Series | None = None,
) -> dict:
    """
    Inverte no lugar os coeficientes da LR cujo sinal contradiz SINAIS_CLINICOS
    e recalibra o intercepto para que a p média em X_ref permaneça a mesma.
    """
    if X_ref is None or y_ref is None:
        X_ref, y_ref = carregar_treino_referencia()
    X_ref = X_ref[FEATURES_MODELO_X]

    clf = pipeline.named_steps["clf"]
    coef = np.array(clf.coef_[0], dtype=float)
    invertidos: list[str] = []
    for i, feature in enumerate(FEATURES_MODELO_X):
        sinal = SINAIS_CLINICOS.get(feature)
        if sinal is None:
            continue
        if sinal > 0 and coef[i] < 0:
            coef[i] *= -1.0
            invertidos.append(feature)
        elif sinal < 0 and coef[i] > 0:
            coef[i] *= -1.0
            invertidos.append(feature)

    p_media_alvo = float(pipeline.predict_proba(X_ref)[:, 1].mean())

    clf.coef_ = coef.reshape(1, -1)

    transformado = pipeline.named_steps["scaler"].transform(
        pipeline.named_steps["imputer"].transform(X_ref)
    )
    logits_sem_intercepto = transformado @ coef

    def desvio_media(intercepto: float) -> float:
        p = 1.0 / (1.0 + np.exp(-(intercepto + logits_sem_intercepto)))
        return abs(float(p.mean()) - p_media_alvo)

    ajuste = minimize_scalar(desvio_media, bounds=(-8.0, 8.0), method="bounded")
    clf.intercept_ = np.array([float(ajuste.x)])
    return {
        "coeficientes_invertidos": invertidos,
        "intercepto_recalibrado": round(float(ajuste.x), 10),
        "p_media_alvo": round(p_media_alvo, 6),
    }
