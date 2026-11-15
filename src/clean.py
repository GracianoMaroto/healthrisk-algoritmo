"""
Módulo de integração relacional (SEQN) e limpeza clínica dos microdados NHANES 2017-2018.
Implementa integralmente a seção 3 (Pipeline de Tratamento) da Documentação Técnica do Bloco 2:
- Junção 1:1 a partir de DEMO_J com validação de integridade referencial
- Decodificação específica de sentinelas (recusa / não sabe) respeitando cada codebook
- Filtro de universo adulto (idade >= 18 anos e exclusão de gestantes)
- Auditoria de inconsistências lógicas e aplicação de limites clínicos plausíveis
- Definição do alvo binário (diabetes) e isolamento estrito contra Data Leakage
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.extract_nhanes import carregar_nhanes_local

ROOT_DIR = Path(__file__).resolve().parent.parent
INTERIM_DIR = ROOT_DIR / "data" / "interim"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

ORDEM_MERGE = [
    "bmx", "bpx", "tchol", "hdl", "trigly",
    "ghb", "glu", "diq", "dr1tot", "dbq",
    "paq", "smq", "alq", "mcq", "fsq",
]

# Colunas utilizadas de cada arquivo para evitar colisão de variáveis administrativas (ex.: WTSAF2YR duplicado)
COLUNAS_SELECIONADAS: dict[str, list[str]] = {
    "demo": [
        "SEQN", "RIAGENDR", "RIDAGEYR", "RIDRETH3", "DMDEDUC2",
        "RIDEXPRG", "INDFMPIR", "WTINT2YR", "WTMEC2YR", "SDMVPSU", "SDMVSTRA",
    ],
    "bmx": ["SEQN", "BMXWT", "BMXHT", "BMXBMI", "BMXWAIST"],
    "bpx": ["SEQN", "BPXSY1", "BPXDI1", "BPXSY2", "BPXDI2", "BPXSY3", "BPXDI3"],
    "tchol": ["SEQN", "LBXTC"],
    "hdl": ["SEQN", "LBDHDD"],
    "trigly": ["SEQN", "LBXTR", "LBDLDL"],
    "ghb": ["SEQN", "LBXGH"],
    "glu": ["SEQN", "LBXGLU"],
    "diq": ["SEQN", "DIQ010", "DID040", "DIQ050", "DIQ070"],
    "dr1tot": ["SEQN", "DR1TKCAL", "DR1TSUGR", "DR1TFIBE", "DR1TSODI", "DR1TSFAT", "DR1TPROT", "DR1TCARB"],
    "dbq": ["SEQN", "DBD895", "DBD900", "DBQ700"],
    "paq": [
        "SEQN",
        "PAQ605", "PAQ610", "PAD615",
        "PAQ620", "PAQ625", "PAD630",
        "PAQ635", "PAQ640", "PAD645",
        "PAQ650", "PAQ655", "PAD660",
        "PAQ665", "PAQ670", "PAD675",
        "PAD680",
    ],
    "smq": ["SEQN", "SMQ020", "SMQ040"],
    "alq": ["SEQN", "ALQ111", "ALQ121"],
    "mcq": ["SEQN", "MCQ300C"],
    "fsq": ["SEQN", "FSDHH", "FSDAD"],
}

SENTINELAS_PADRAO = {7, 9, 77, 99, 777, 999, 7777, 9999}


def recodificar_sentinelas(serie: pd.Series, codigos_bloqueio: set[int | float]) -> pd.Series:
    """
    Substitui códigos sentinelas de recusa/não sabe por NaN, preservando zeros
    reais e valores clínicos legítimos conforme codebook do arquivo NHANES.
    """
    return serie.where(~serie.isin(codigos_bloqueio), np.nan)


def integrar_nhanes(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Integra os 16 módulos do NHANES pela chave primária SEQN com validação 1:1
    e verificação de integridade referencial (Seções 2.2.3 e 3.4 do Bloco 2).
    """
    base = frames["demo"][COLUNAS_SELECIONADAS["demo"]].copy()
    assert base["SEQN"].is_unique, "Falha de integridade: SEQN duplicado em DEMO_J"

    seqn_universo = set(base["SEQN"])
    for nome in ORDEM_MERGE:
        df_mod = frames[nome][COLUNAS_SELECIONADAS[nome]].copy()
        assert df_mod["SEQN"].is_unique, f"Falha de integridade: SEQN duplicado em {nome}"
        orfaos = set(df_mod["SEQN"]) - seqn_universo
        assert len(orfaos) == 0, f"Falha referencial: {len(orfaos)} SEQNs em {nome} ausentes em DEMO_J"

        base = base.merge(
            df_mod,
            on="SEQN",
            how="left",
            validate="one_to_one",
        )

    colunas_duplicadas = [c for c in base.columns if c.endswith("_x") or c.endswith("_y")]
    assert len(colunas_duplicadas) == 0, f"Join duplicou colunas: {colunas_duplicadas}"
    return base


def executar_limpeza(frames: dict[str, pd.DataFrame] | None = None) -> tuple[pd.DataFrame, dict]:
    """
    Executa todas as etapas do pipeline de limpeza (Seção 3.1 a 3.9 do Bloco 2),
    salva o dataset intermediário em data/interim/nhanes_limpo.parquet e retorna
    o DataFrame acompanhado do relatório auditável de qualidade.
    """
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if frames is None:
        frames = carregar_nhanes_local()

    df_bruto = integrar_nhanes(frames)
    n_total_bruto = len(df_bruto)

    # 1. Decodificação de sentinelas específicas por codebook (Seção 3.3)
    # Categóricas com códigos 7/9 (Recusou / Não sabe)
    cols_cat_7_9 = [
        "DMDEDUC2", "DIQ010", "DIQ050", "DIQ070", "DBQ700",
        "PAQ605", "PAQ620", "PAQ635", "PAQ650", "PAQ665",
        "SMQ020", "SMQ040", "ALQ111", "MCQ300C", "FSDHH", "FSDAD",
    ]
    for col in cols_cat_7_9:
        df_bruto[col] = recodificar_sentinelas(df_bruto[col], {7, 9, 77, 99})

    # Dias por semana no PAQ (1 a 7 são dias reais! Apenas 77 e 99 são sentinelas!)
    cols_dias_paq = ["PAQ610", "PAQ625", "PAQ640", "PAQ655", "PAQ670"]
    for col in cols_dias_paq:
        df_bruto[col] = recodificar_sentinelas(df_bruto[col], {77, 99, 777, 999, 7777, 9999})

    # Minutos por dia no PAQ (7777 e 9999 são sentinelas)
    cols_min_paq = ["PAD615", "PAD630", "PAD645", "PAD660", "PAD675", "PAD680"]
    for col in cols_min_paq:
        df_bruto[col] = recodificar_sentinelas(df_bruto[col], {7777, 9999})

    # Comportamento alimentar DBQ (DBD895 / DBD900: 5555 = >21 refeições -> truncado em 21; 7777/9999 -> NaN)
    for col in ["DBD895", "DBD900"]:
        df_bruto[col] = recodificar_sentinelas(df_bruto[col], {7777, 9999})
        df_bruto[col] = df_bruto[col].replace({5555: 21.0})

    # Frequência de álcool ALQ121 (77 e 99 são sentinelas)
    df_bruto["ALQ121"] = recodificar_sentinelas(df_bruto["ALQ121"], {77, 99})

    # 2. Filtro de universo: adultos (RIDAGEYR >= 18) e exclusão de gestantes (RIDEXPRG == 1)
    mask_adulto = df_bruto["RIDAGEYR"] >= 18
    n_menores = int((~mask_adulto).sum())
    df = df_bruto.loc[mask_adulto].copy()

    mask_gestante = df["RIDEXPRG"] == 1
    n_gestantes = int(mask_gestante.sum())
    df = df.loc[~mask_gestante].copy()
    n_universo_adulto = len(df)

    # 3. Padronização de nomes e unidades (Seção 3.2 - Quadro 4)
    # Pressão arterial: primeira medida válida ou média das medidas disponíveis
    pas_cols = ["BPXSY1", "BPXSY2", "BPXSY3"]
    pad_cols = ["BPXDI1", "BPXDI2", "BPXDI3"]
    # No NHANES, PAD == 0 indica leitura ausente/inaudível (K5 ausente)
    for c in pad_cols:
        df[c] = df[c].where(df[c] > 0, np.nan)

    df["pas_mmhg"] = df[pas_cols].mean(axis=1)
    df["pad_mmhg"] = df[pad_cols].mean(axis=1)

    renomear = {
        "SEQN": "id_participante",
        "RIDAGEYR": "idade_anos",
        "RIAGENDR": "sexo",
        "RIDRETH3": "etnia",
        "DMDEDUC2": "escolaridade_ord",
        "INDFMPIR": "razao_renda_pobreza",
        "BMXWT": "peso_kg",
        "BMXHT": "altura_cm",
        "BMXBMI": "imc",
        "BMXWAIST": "cintura_cm",
        "LBXTC": "colesterol_total",
        "LBDHDD": "hdl",
        "LBXTR": "triglicerideos",
        "LBDLDL": "ldl",
        "DR1TSUGR": "acucar_g_dia",
        "DR1TFIBE": "fibra_g_dia",
        "DR1TSODI": "sodio_mg_dia",
        "DR1TSFAT": "gordura_sat_g_dia",
        "DR1TKCAL": "energia_kcal",
        "PAD680": "minutos_sentado",
        "LBXGH": "hba1c",
        "LBXGLU": "glicemia_jejum",
        "DIQ010": "diabetes_autorrelato",
        "DIQ050": "usa_insulina",
        "DIQ070": "usa_hipoglicemiante",
        "DID040": "idade_diagnostico",
    }
    df = df.rename(columns=renomear)

    # 4. Auditoria de inconsistências lógicas e outliers clínicos (Seções 3.5 e 3.6)
    contagem_outliers: dict[str, int] = {}

    # a) Altura < 120 ou > 210 cm
    inv_altura = (df["altura_cm"] < 120) | (df["altura_cm"] > 210)
    contagem_outliers["altura_fora_120_210cm"] = int(inv_altura.sum())
    df.loc[inv_altura, "altura_cm"] = np.nan

    # b) Peso < 30 ou > 250 kg
    inv_peso = (df["peso_kg"] < 30) | (df["peso_kg"] > 250)
    contagem_outliers["peso_fora_30_250kg"] = int(inv_peso.sum())
    df.loc[inv_peso, "peso_kg"] = np.nan

    # c) Recálculo e consistência de IMC
    imc_calc = df["peso_kg"] / ((df["altura_cm"] / 100.0) ** 2)
    div_imc = (df["imc"] - imc_calc).abs() > 1.0
    contagem_outliers["imc_divergente_recalculo"] = int(div_imc.sum())
    df["imc"] = df["imc"].fillna(imc_calc)
    df.loc[div_imc & imc_calc.notna(), "imc"] = imc_calc.loc[div_imc & imc_calc.notna()]
    inv_imc = (df["imc"] < 12) | (df["imc"] > 80)
    contagem_outliers["imc_fora_12_80"] = int(inv_imc.sum())
    df.loc[inv_imc, "imc"] = np.nan

    # d) Cintura fora de 50-180 cm
    inv_cint = (df["cintura_cm"] < 50) | (df["cintura_cm"] > 180)
    contagem_outliers["cintura_fora_50_180cm"] = int(inv_cint.sum())
    df.loc[inv_cint, "cintura_cm"] = np.nan

    # e) Pressão sistólica < diastólica ou fora de limites clínicos (PAS 70-250, PAD 40-150)
    inv_pa_logica = df["pas_mmhg"] <= df["pad_mmhg"]
    inv_pas = (df["pas_mmhg"] < 70) | (df["pas_mmhg"] > 250) | inv_pa_logica
    inv_pad = (df["pad_mmhg"] < 40) | (df["pad_mmhg"] > 150) | inv_pa_logica
    contagem_outliers["pressao_inconsistente_ou_extrema"] = int((inv_pas | inv_pad).sum())
    df.loc[inv_pas, "pas_mmhg"] = np.nan
    df.loc[inv_pad, "pad_mmhg"] = np.nan

    # f) Minutos sentado > 1440 min/dia
    inv_sentado = (df["minutos_sentado"] < 0) | (df["minutos_sentado"] > 1440)
    contagem_outliers["minutos_sentado_maior_1440"] = int(inv_sentado.sum())
    df.loc[inv_sentado, "minutos_sentado"] = np.nan

    # g) Energia dietética implausível (< 500 ou > 6000 kcal) e açúcar > 400 g
    inv_kcal = (df["energia_kcal"] < 500) | (df["energia_kcal"] > 6000)
    contagem_outliers["energia_fora_500_6000kcal"] = int(inv_kcal.sum())
    df.loc[inv_kcal, "energia_kcal"] = np.nan

    inv_acucar = (df["acucar_g_dia"] < 0) | (df["acucar_g_dia"] > 400)
    contagem_outliers["acucar_maior_400g"] = int(inv_acucar.sum())
    df.loc[inv_acucar, "acucar_g_dia"] = np.nan

    # Flag de inconsistência registrada para auditoria
    df["flag_inconsistencia_tratada"] = (
        inv_altura | inv_peso | div_imc | inv_cint | inv_pas | inv_pad | inv_sentado | inv_kcal | inv_acucar
    ).astype(int)

    # 5. Exclusão de registros sem antropometria válida ou sem elementos para definir o alvo
    # Premissa 1.4b do Bloco 2: "participantes com 18 anos ou mais e com medidas antropométricas válidas"
    mask_antropometria_valida = df["imc"].notna() & df["cintura_cm"].notna()
    n_sem_antropometria = int((~mask_antropometria_valida).sum())
    df = df.loc[mask_antropometria_valida].copy()

    # 6. Construção do alvo binário diabetes (Seção 3.9 do Bloco 2)
    # diabetes = 1 se DIQ010 == 1 OU LBXGH >= 6.5 OU LBXGLU >= 126
    crit_autorrelato = df["diabetes_autorrelato"] == 1
    crit_hba1c = df["hba1c"] >= 6.5
    crit_glicemia = df["glicemia_jejum"] >= 126.0

    # Verifica se há pelo menos um critério avaliável (autorrelato ou laboratório)
    tem_criterio_alvo = df["diabetes_autorrelato"].notna() | df["hba1c"].notna() | df["glicemia_jejum"].notna()
    n_sem_alvo = int((~tem_criterio_alvo).sum())
    df = df.loc[tem_criterio_alvo].copy()

    df["diabetes"] = (
        (df["diabetes_autorrelato"] == 1)
        | (df["hba1c"] >= 6.5)
        | (df["glicemia_jejum"] >= 126.0)
    ).astype(int)

    # Alvo secundário de 3 classes (0 = normoglicêmico, 1 = pré-diabetes/borderline, 2 = diabetes)
    # para análise exploratória complementar citada na seção 3.9
    pre_diab = (
        (df["diabetes"] == 0)
        & (
            (df["diabetes_autorrelato"] == 3)
            | ((df["hba1c"] >= 5.7) & (df["hba1c"] < 6.5))
            | ((df["glicemia_jejum"] >= 100.0) & (df["glicemia_jejum"] < 126.0))
        )
    )
    df["perfil_glicemico_3classes"] = np.where(
        df["diabetes"] == 1, 2, np.where(pre_diab, 1, 0)
    )

    caminho_interim = INTERIM_DIR / "nhanes_limpo.parquet"
    df.to_parquet(caminho_interim, index=False)

    relatorio = {
        "n_total_demo_bruto": n_total_bruto,
        "n_excluidos_menores_18": n_menores,
        "n_excluidos_gestantes": n_gestantes,
        "n_universo_adulto_nao_gestante": n_universo_adulto,
        "n_excluidos_sem_antropometria_valida": n_sem_antropometria,
        "n_excluidos_sem_criterio_alvo": n_sem_alvo,
        "n_amostra_analitica_final": int(len(df)),
        "prevalencia_diabetes_amostra_pct": round(float(df["diabetes"].mean() * 100), 2),
        "n_casos_diabetes": int(df["diabetes"].sum()),
        "n_controles_sem_diabetes": int((df["diabetes"] == 0).sum()),
        "detalhamento_criterios_alvo": {
            "autorrelato_diq010_eq_1": int((df["diabetes_autorrelato"] == 1).sum()),
            "hba1c_ge_6_5": int((df["hba1c"] >= 6.5).sum()),
            "glicemia_jejum_ge_126": int((df["glicemia_jejum"] >= 126.0).sum()),
            "casos_ocultos_apenas_exame_sem_autorrelato": int(
                ((df["diabetes"] == 1) & (df["diabetes_autorrelato"] != 1)).sum()
            ),
        },
        "outliers_e_inconsistencias_convertidos_nan": contagem_outliers,
    }

    (PROCESSED_DIR / "relatorio_qualidade_limpeza.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"[Limpeza] Bruto={n_total_bruto} -> Adultos não gestantes={n_universo_adulto} "
        f"-> Amostra Analítica={len(df)} | Casos Diabetes={relatorio['n_casos_diabetes']} "
        f"({relatorio['prevalencia_diabetes_amostra_pct']}%)"
    )
    return df, relatorio


if __name__ == "__main__":
    executar_limpeza()
