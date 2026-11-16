"""
Exporta o artefato on-device da Regressão Logística para o HealthRisk Mobile.

Carrega models/logistic_regression.joblib (Pipeline com StratifiedMedianImputer +
StandardScaler + LogisticRegression) e grava artifacts/mobile_lr_bundle.json com:

- ordem das 19 features
- medianas estratificadas do imputador
- mean_ / scale_ do scaler
- coef_ e intercept_
- parâmetros da dieta (média/desvio do treino)
- tercis e limiar 0,40
- goldens Python (alto, moderado, baixo) com p esperado

O .joblib NÃO deve ser copiado para o app Flutter.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.features import FEATURES_MODELO_X, StratifiedMedianImputer  # noqa: F401
from src.monotonia_clinica import aplicar_monotonia_clinica, carregar_treino_referencia

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

# Tabela de equivalência congelada (pergunta de tela → gramas / MET / minutos).
# O app Dart precisa repetir estes números à risca.
TABELA_EQUIVALENCIA = {
    "kcal_referencia": 2000.0,
    "fibra_hortalica_sim_g": 28.0,
    "fibra_hortalica_nao_g": 10.0,
    "acucar_bebida_frequente_g": 145.0,
    "acucar_bebida_rara_g": 60.0,
    "sodio_embutido_frequente_mg": 4200.0,
    "sodio_embutido_raro_mg": 1900.0,
    "gordura_sat_ultraprocessado_g": 36.0,
    "gordura_sat_protegido_g": 18.0,
    "refeicoes_prontas_frequente": 6.0,
    "refeicoes_prontas_raro": 1.0,
    "met_cumpre_oms": 600.0,
    "met_nao_cumpre": 140.0,
    "minutos_sentado_alto": 540.0,
    "minutos_sentado_baixo": 240.0,
}


def _indice_qualidade_dieta(
    fibra_g: float, acucar_g: float, sodio_mg: float, gsat_g: float, params_dieta: dict
) -> float:
    z_fb = (fibra_g - params_dieta["fibra_g_dia"]["media_treino"]) / params_dieta["fibra_g_dia"]["std_treino"]
    z_ac = (acucar_g - params_dieta["acucar_g_dia"]["media_treino"]) / params_dieta["acucar_g_dia"]["std_treino"]
    z_so = (sodio_mg - params_dieta["sodio_mg_dia"]["media_treino"]) / params_dieta["sodio_mg_dia"]["std_treino"]
    z_gs = (gsat_g - params_dieta["gordura_sat_g_dia"]["media_treino"]) / params_dieta["gordura_sat_g_dia"]["std_treino"]
    return (z_fb - z_ac - z_so - z_gs) / 4.0


def traduzir_perguntas(respostas: dict, params_dieta: dict) -> dict[str, float]:
    """Mesmo contrato que lib/domain/tradutor_perguntas.dart."""
    eq = TABELA_EQUIVALENCIA
    kcal = eq["kcal_referencia"]
    fibra = eq["fibra_hortalica_sim_g"] if respostas["hortalica_quase_todo_dia"] else eq["fibra_hortalica_nao_g"]
    acucar = (
        eq["acucar_bebida_frequente_g"]
        if respostas["bebida_acucarada_frequente"]
        else eq["acucar_bebida_rara_g"]
    )
    sodio = (
        eq["sodio_embutido_frequente_mg"]
        if respostas["embutido_frequente"]
        else eq["sodio_embutido_raro_mg"]
    )
    ultraprocessado = respostas["comida_pronta_frequente"] or respostas["embutido_frequente"]
    gsat = eq["gordura_sat_ultraprocessado_g"] if ultraprocessado else eq["gordura_sat_protegido_g"]
    refeicao_pronta = (
        eq["refeicoes_prontas_frequente"]
        if respostas["comida_pronta_frequente"]
        else eq["refeicoes_prontas_raro"]
    )
    met = eq["met_cumpre_oms"] if respostas["cumpre_150_min"] else eq["met_nao_cumpre"]
    sentado = (
        eq["minutos_sentado_alto"]
        if respostas["sentado_8h_ou_mais"]
        else eq["minutos_sentado_baixo"]
    )

    peso = float(respostas["peso_kg"])
    altura = float(respostas["altura_cm"])
    cintura = float(respostas["cintura_cm"])
    imc = peso / ((altura / 100.0) ** 2)
    rce = cintura / altura

    vetor: dict[str, float] = {
        "idade_anos": float(respostas["idade_anos"]),
        "sexo": float(respostas["sexo"]),
        "escolaridade_ord": (
            float("nan") if respostas.get("escolaridade_ord") is None else float(respostas["escolaridade_ord"])
        ),
        "razao_renda_pobreza": float("nan"),  # renda não é perguntada no celular
        "inseguranca_alimentar": (
            float("nan")
            if respostas.get("inseguranca_alimentar") is None
            else float(respostas["inseguranca_alimentar"])
        ),
        "densidade_acucar": (acucar / kcal) * 1000.0,
        "densidade_fibra": (fibra / kcal) * 1000.0,
        "excesso_sodio": 1.0 if sodio >= 2300.0 else 0.0,
        "indice_qualidade_dieta": _indice_qualidade_dieta(fibra, acucar, sodio, gsat, params_dieta),
        "refeicao_pronta": float(refeicao_pronta),
        "met_min_semana": float(met),
        "cumpre_oms_150": 1.0 if met >= 600.0 else 0.0,
        "minutos_sentado": float(sentado),
        "sedentarismo_alto": 1.0 if sentado >= 480.0 else 0.0,
        "imc": float(imc),
        "razao_cintura_estatura": float(rce),
        "pressao_alta": 1.0 if respostas["pressao_alta"] else 0.0,
        "hdl": float("nan") if respostas.get("hdl") is None else float(respostas["hdl"]),
        "historico_familiar_diabetes": 1.0 if respostas["familiar_primeiro_grau"] else 0.0,
    }
    return vetor


def _faixa(p: float, tercil_inf: float, tercil_sup: float) -> str:
    if p <= tercil_inf:
        return "baixo"
    if p <= tercil_sup:
        return "moderado"
    return "alto"


def _json_safe(valor):
    if isinstance(valor, dict):
        return {str(k): _json_safe(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_safe(v) for v in valor]
    if isinstance(valor, (np.floating, float)):
        numero = float(valor)
        if np.isnan(numero):
            return None
        return round(numero, 10)
    if isinstance(valor, (np.integer, int)):
        return int(valor)
    if isinstance(valor, np.ndarray):
        return [_json_safe(v) for v in valor.tolist()]
    return valor


def exportar() -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics = json.loads((PROCESSED_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    thresholds = json.loads((MODELS_DIR / "risk_thresholds.json").read_text(encoding="utf-8"))
    params_dieta = metrics["parametros_indice_dieta_treino"]
    tercil_inf = float(thresholds["tercil_inferior_baixo_moderado"])
    tercil_sup = float(thresholds["tercil_superior_moderado_alto"])
    limiar = float(thresholds["limiar_triagem_sensibilidade"])

    pipe = joblib.load(MODELS_DIR / "logistic_regression.joblib")
    X_treino, y_treino = carregar_treino_referencia()
    info_monotonia = aplicar_monotonia_clinica(pipe, X_treino, y_treino)
    print(f"[Monotonia] coeficientes invertidos: {info_monotonia['coeficientes_invertidos']}")
    imputer: StratifiedMedianImputer = pipe.named_steps["imputer"]
    scaler = pipe.named_steps["scaler"]
    clf = pipe.named_steps["clf"]

    # Três perfis de tela (vocabulário da pessoa). O vetor de 19 features é montado
    # pela tabela de equivalência; a probabilidade vem da LR treinada.
    goldens_respostas = {
        "alto": {
            "idade_anos": 58,
            "sexo": 1,
            "peso_kg": 96.0,
            "altura_cm": 170.0,
            "cintura_cm": 112.0,
            "familiar_primeiro_grau": True,
            "pressao_alta": True,
            "diagnostico_informado": False,
            "cumpre_150_min": False,
            "sentado_8h_ou_mais": True,
            "hortalica_quase_todo_dia": False,
            "comida_pronta_frequente": True,
            "bebida_acucarada_frequente": True,
            "embutido_frequente": True,
            "escolaridade_ord": 2,
            "hdl": 38.0,
            "inseguranca_alimentar": 1.0,
        },
        "moderado": {
            "idade_anos": 46,
            "sexo": 1,
            "peso_kg": 86.0,
            "altura_cm": 175.0,
            "cintura_cm": 99.0,
            "familiar_primeiro_grau": True,
            "pressao_alta": False,
            "diagnostico_informado": False,
            "cumpre_150_min": True,
            "sentado_8h_ou_mais": True,
            "hortalica_quase_todo_dia": False,
            "comida_pronta_frequente": True,
            "bebida_acucarada_frequente": False,
            "embutido_frequente": False,
            "escolaridade_ord": 4,
            "hdl": 46.0,
            "inseguranca_alimentar": 0.0,
        },
        "baixo": {
            "idade_anos": 29,
            "sexo": 2,
            "peso_kg": 61.0,
            "altura_cm": 165.0,
            "cintura_cm": 74.0,
            "familiar_primeiro_grau": False,
            "pressao_alta": False,
            "diagnostico_informado": False,
            "cumpre_150_min": True,
            "sentado_8h_ou_mais": False,
            "hortalica_quase_todo_dia": True,
            "comida_pronta_frequente": False,
            "bebida_acucarada_frequente": False,
            "embutido_frequente": False,
            "escolaridade_ord": 5,
            "hdl": 62.0,
            "inseguranca_alimentar": 0.0,
        },
    }

    goldens = []
    for nome, respostas in goldens_respostas.items():
        vetor = traduzir_perguntas(respostas, params_dieta)
        X = pd.DataFrame([vetor], columns=FEATURES_MODELO_X)
        p = float(pipe.predict_proba(X)[0, 1])
        faixa = _faixa(p, tercil_inf, tercil_sup)
        goldens.append(
            {
                "id": nome,
                "respostas_tela": respostas,
                "vetor_19": {k: (None if (isinstance(v, float) and np.isnan(v)) else round(float(v), 10)) for k, v in vetor.items()},
                "p": round(p, 10),
                "faixa": faixa,
            }
        )
        print(f"[Golden] {nome:<9} p={p:.6f} faixa={faixa}")

    faixas = {g["id"]: g["faixa"] for g in goldens}
    if faixas.get("alto") != "alto" or faixas.get("baixo") != "baixo":
        raise SystemExit(
            f"Goldens não caíram nas faixas esperadas: {faixas}. "
            "Ajuste os perfis de tela antes de congelar o JSON."
        )

    bundle = {
        "modelo": "regressao_logistica",
        "n_features": len(FEATURES_MODELO_X),
        "features": FEATURES_MODELO_X,
        "imputer": {
            "medianas_estrato": _json_safe(imputer.medianas_estrato_),
            "medianas_globais": _json_safe(imputer.medianas_globais_),
        },
        "scaler": {
            "mean": [round(float(x), 10) for x in scaler.mean_],
            "scale": [round(float(x), 10) for x in scaler.scale_],
        },
        "classificador": {
            "coef": [round(float(x), 10) for x in clf.coef_[0]],
            "intercept": round(float(clf.intercept_[0]), 10),
        },
        "parametros_dieta": params_dieta,
        "tabela_equivalencia": TABELA_EQUIVALENCIA,
        "limiares": {
            "tercil_inferior_baixo_moderado": tercil_inf,
            "tercil_superior_moderado_alto": tercil_sup,
            "limiar_triagem_sensibilidade": limiar,
        },
        "fatores_acionaveis": [
            "idade_anos",
            "razao_cintura_estatura",
            "historico_familiar_diabetes",
            "densidade_acucar",
            "densidade_fibra",
            "excesso_sodio",
            "indice_qualidade_dieta",
            "refeicao_pronta",
            "met_min_semana",
            "cumpre_oms_150",
            "minutos_sentado",
            "sedentarismo_alto",
            "imc",
            "pressao_alta",
        ],
        "fatores_nao_exibidos": [
            "sexo",
            "escolaridade_ord",
            "razao_renda_pobreza",
        ],
        "goldens": goldens,
        "monotonia_clinica": _json_safe(info_monotonia),
        "metricas_referencia": {
            "test_roc_auc": metrics["modelos"]["Regressão Logística"]["test_roc_auc"],
            "recall_limiar_040": metrics["modelos"]["Regressão Logística"]["limiar_rastreio"]["recall_sensibilidade"],
        },
    }

    destino = ARTIFACTS_DIR / "mobile_lr_bundle.json"
    destino.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Export] {destino} ({destino.stat().st_size} bytes)")
    _espelhar_no_app_mobile(destino)
    return destino


def _espelhar_no_app_mobile(origem: Path) -> None:
    destino = (
        ROOT_DIR.parent
        / "Bloco 3 - des mobile"
        / "assets"
        / "models"
        / "mobile_lr_bundle.json"
    )
    if not destino.parent.exists():
        return
    destino.write_bytes(origem.read_bytes())
    print(f"[Export] espelhado em {destino}")


if __name__ == "__main__":
    exportar()
