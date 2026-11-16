"""Diagnóstico temporário: monotonia após correção clínica."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.export_mobile_artifacts import traduzir_perguntas
from src.features import FEATURES_MODELO_X
from src.monotonia_clinica import aplicar_monotonia_clinica, carregar_treino_referencia

ROOT = Path(__file__).resolve().parent
metrics = json.loads((ROOT / "data/processed/model_metrics.json").read_text(encoding="utf-8"))
params_dieta = metrics["parametros_indice_dieta_treino"]
lr = joblib.load(ROOT / "models/logistic_regression.joblib")
X_tr, y_tr = carregar_treino_referencia()
aplicar_monotonia_clinica(lr, X_tr, y_tr)

base = {
    "idade_anos": 25,
    "sexo": 2,
    "peso_kg": 62.0,
    "altura_cm": 165.0,
    "cintura_cm": 76.0,
    "familiar_primeiro_grau": False,
    "pressao_alta": False,
    "diagnostico_informado": False,
    "cumpre_150_min": False,
    "sentado_8h_ou_mais": False,
    "hortalica_quase_todo_dia": False,
    "comida_pronta_frequente": False,
    "bebida_acucarada_frequente": False,
    "embutido_frequente": False,
    "escolaridade_ord": 4,
    "hdl": 55.0,
    "inseguranca_alimentar": 0.0,
}


def score(respostas):
    vetor = traduzir_perguntas(respostas, params_dieta)
    X = pd.DataFrame([vetor], columns=FEATURES_MODELO_X)
    return float(lr.predict_proba(X)[0, 1])


print("BASE:", round(score(base) * 100, 2))
b = score(base)
toggles = {
    "cumpre_150_min": True,
    "sentado_8h_ou_mais": True,
    "hortalica_quase_todo_dia": True,
    "comida_pronta_frequente": True,
    "bebida_acucarada_frequente": True,
    "embutido_frequente": True,
}
for k, val in toggles.items():
    r = dict(base)
    r[k] = val
    s = score(r)
    print(f"  {k}={val}: {s*100:.2f}% (d={(s-b)*100:+.2f})")

unhealthy = dict(base)
unhealthy.update(
    {
        "cumpre_150_min": False,
        "sentado_8h_ou_mais": True,
        "hortalica_quase_todo_dia": False,
        "comida_pronta_frequente": True,
        "bebida_acucarada_frequente": True,
        "embutido_frequente": True,
    }
)
healthy = dict(base)
healthy.update(
    {
        "cumpre_150_min": True,
        "sentado_8h_ou_mais": False,
        "hortalica_quase_todo_dia": True,
        "comida_pronta_frequente": False,
        "bebida_acucarada_frequente": False,
        "embutido_frequente": False,
    }
)
print("6 RUINS:", round(score(unhealthy) * 100, 2))
print("6 BOAS :", round(score(healthy) * 100, 2))
print("\nidade x exercicio:")
for idade in [22, 25, 28]:
    r = dict(base)
    r["idade_anos"] = idade
    s0 = score({**r, "cumpre_150_min": False})
    s1 = score({**r, "cumpre_150_min": True})
    print(f"  {idade}: sem {s0*100:.2f}% | com {s1*100:.2f}%")
