"""
Módulo de Engenharia de Features, Auditoria de Qualidade e Escudo Anti-Vazamento (Data Leakage Shield).
Implementa integralmente a seção 4 da Documentação Técnica do Bloco 2:
- Eixo 1: Hábitos alimentares (densidades por 1000 kcal, metas OMS/FDA, refeições prontas, índice de qualidade)
- Eixo 2: Atividade física e sedentarismo (MET-min/semana, meta 150 min OMS, perfil de movimento)
- Eixo 3: Proxies geográfico-sociais individuais (renda/pobreza, escolaridade, insegurança alimentar)
- Cofatores clínicos de rotina (IMC, razão cintura/estatura, pressão alta medida, HDL, histórico familiar)
- Geração de analytic.parquet, data_dictionary.csv, leakage_blocklist.txt e feature_audit.csv
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from src.clean import executar_limpeza


class StratifiedMedianImputer(BaseEstimator, TransformerMixin):
    """
    Imputador customizado que implementa a regra da seção 3.7 (Quadro 6) do Bloco 2:
    calcula a mediana estratificada por sexo e faixa etária exclusivamente no conjunto
    de treino (fit) e aplica os parâmetros congelados no conjunto de teste (transform),
    impedindo vazamento estatístico entre treino e teste.
    """

    def __init__(self, feature_names: list[str]):
        self.feature_names = feature_names

    def _criar_estrato(self, df: pd.DataFrame) -> pd.Series:
        faixa = pd.cut(
            df["idade_anos"],
            bins=[0, 29, 44, 59, 150],
            labels=["18-29", "30-44", "45-59", "60+"],
        ).astype(str)
        sexo_str = df["sexo"].fillna(1).astype(int).astype(str)
        return sexo_str + "_" + faixa

    def fit(self, X: pd.DataFrame | np.ndarray, y=None):
        df = pd.DataFrame(X, columns=self.feature_names).copy()
        estrato = self._criar_estrato(df)
        self.medianas_estrato_: dict[str, dict[str, float]] = {}
        self.medianas_globais_: dict[str, float] = {}

        for col in self.feature_names:
            self.medianas_globais_[col] = float(df[col].median())
            med_por_grupo = df.groupby(estrato)[col].median().to_dict()
            self.medianas_estrato_[col] = {
                k: float(v) if pd.notna(v) else self.medianas_globais_[col]
                for k, v in med_por_grupo.items()
            }
        return self

    def transform(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        df = pd.DataFrame(X, columns=self.feature_names).copy()
        estrato = self._criar_estrato(df)
        for col in self.feature_names:
            if df[col].isna().any():
                valores_imputados = estrato.map(self.medianas_estrato_[col]).fillna(
                    self.medianas_globais_[col]
                )
                df[col] = df[col].fillna(valores_imputados)
        return df[self.feature_names].to_numpy(dtype=float)

ROOT_DIR = Path(__file__).resolve().parent.parent
INTERIM_DIR = ROOT_DIR / "data" / "interim"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

# Vetor X prioritário definido na seção 4.7 do Bloco 2 (19 variáveis preditoras)
FEATURES_MODELO_X: list[str] = [
    # a) Demográficas e proxies geográfico-sociais (Nível A)
    "idade_anos",
    "sexo",
    "escolaridade_ord",
    "razao_renda_pobreza",
    "inseguranca_alimentar",
    # b) Eixo 1 — Hábitos alimentares
    "densidade_acucar",
    "densidade_fibra",
    "excesso_sodio",
    "indice_qualidade_dieta",
    "refeicao_pronta",
    # c) Eixo 2 — Atividade física e sedentarismo
    "met_min_semana",
    "cumpre_oms_150",
    "minutos_sentado",
    "sedentarismo_alto",
    # d) Cofatores clínicos de rotina permitidos
    "imc",
    "razao_cintura_estatura",
    "pressao_alta",
    "hdl",
    "historico_familiar_diabetes",
]

# Variáveis terminantemente proibidas no vetor X (Data Leakage Shield — Seção 3.9 do Bloco 2)
VARIAVEIS_BLOQUEADAS_VAZAMENTO: list[str] = [
    "DIQ010",
    "LBXGH",
    "LBXGLU",
    "DIQ050",
    "DIQ070",
    "DID040",
    "diabetes_autorrelato",
    "hba1c",
    "glicemia_jejum",
    "usa_insulina",
    "usa_hipoglicemiante",
    "idade_diagnostico",
    "perfil_glicemico_3classes",
    "diabetes",
]


def _bloco_minutos_paq(
    df: pd.DataFrame, col_filtro: str, col_dias: str, col_min: str
) -> pd.Series:
    """
    Calcula minutos semanais de um domínio do PAQ respeitando a regra da seção 4.4 (Quadro 9):
    - Se a pergunta filtro ('praticou?') == 2 ('Não'), o volume semanal é 0.0 legítimo.
    - Se a pergunta filtro == 1 ('Sim'), multiplica dias * minutos/dia (limitando minutos/dia <= 960).
    - Se a pergunta filtro for nula/recusa, retorna NaN (não inventa zero de exercício).
    """
    praticou = df[col_filtro]
    dias = df[col_dias].where((df[col_dias] >= 1) & (df[col_dias] <= 7), np.nan)
    minutos = df[col_min].where((df[col_min] >= 0) & (df[col_min] <= 960), np.nan)
    produto = dias * minutos

    resultado = pd.Series(np.nan, index=df.index, dtype="float64")
    resultado.loc[praticou == 2] = 0.0
    mask_sim = (praticou == 1) & produto.notna()
    resultado.loc[mask_sim] = produto.loc[mask_sim]
    return resultado


def construir_features(df_limpo: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Constrói todas as variáveis derivadas dos Eixos 1, 2, 3 e cofatores clínicos,
    audita a ausência de vazamento e persiste os artefatos em data/processed/.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if df_limpo is None:
        caminho_interim = INTERIM_DIR / "nhanes_limpo.parquet"
        if caminho_interim.exists():
            df = pd.read_parquet(caminho_interim)
        else:
            df, _ = executar_limpeza()
    else:
        df = df_limpo.copy()

    # -------------------------------------------------------------------------
    # 4.2 Features Demográficas e Socioeconômicas (Eixo 3 - Nível A)
    # -------------------------------------------------------------------------
    # Faixa etária gerencial: 18-29, 30-44, 45-59, 60+
    df["faixa_etaria"] = pd.cut(
        df["idade_anos"],
        bins=[17, 29, 44, 59, 120],
        labels=["18-29", "30-44", "45-59", "60+"],
    ).astype(str)

    # Insegurança alimentar domiciliar (FSDHH: 1 = segurança plena -> 0; 2,3,4 = algum grau de insegurança -> 1)
    df["inseguranca_alimentar"] = np.where(
        df["FSDHH"].isna(),
        np.nan,
        np.where(df["FSDHH"] > 1, 1.0, 0.0),
    )

    # -------------------------------------------------------------------------
    # 4.3 Eixo 1 — Hábitos Alimentares (Quadro 8)
    # -------------------------------------------------------------------------
    # Se energia_kcal for nula (incluindo os <500 ou >6000 zerados na limpeza), densidades viram NaN
    kcal_valida = df["energia_kcal"].where(df["energia_kcal"] >= 500, np.nan)
    df["densidade_acucar"] = (df["acucar_g_dia"] / kcal_valida) * 1000.0
    df["densidade_fibra"] = (df["fibra_g_dia"] / kcal_valida) * 1000.0

    df["meta_fibra"] = np.where(
        df["fibra_g_dia"].isna(), np.nan, (df["fibra_g_dia"] >= 25.0).astype(float)
    )
    df["excesso_sodio"] = np.where(
        df["sodio_mg_dia"].isna(), np.nan, (df["sodio_mg_dia"] >= 2300.0).astype(float)
    )

    # Refeição pronta / fora de casa na última semana (DBD895, complementado por DBD900 fast-food)
    df["refeicao_pronta"] = df["DBD895"].fillna(df["DBD900"])
    df["dieta_ausente"] = df["energia_kcal"].isna().astype(int)

    # Cálculo preliminar de indice_qualidade_dieta (no treino do modelo é recalculado dentro do Pipeline
    # usando estritamente média e desvio padrão do conjunto de treino!)
    def _z(col: pd.Series) -> pd.Series:
        return (col - col.mean()) / col.std(ddof=0)

    df["indice_qualidade_dieta"] = (
        _z(df["fibra_g_dia"])
        - _z(df["acucar_g_dia"])
        - _z(df["sodio_mg_dia"])
        - _z(df["gordura_sat_g_dia"])
    ) / 4.0

    # -------------------------------------------------------------------------
    # 4.4 Eixo 2 — Atividade Física e Sedentarismo (Quadro 9)
    # -------------------------------------------------------------------------
    vig_trab = _bloco_minutos_paq(df, "PAQ605", "PAQ610", "PAD615")
    mod_trab = _bloco_minutos_paq(df, "PAQ620", "PAQ625", "PAD630")
    desloc = _bloco_minutos_paq(df, "PAQ635", "PAQ640", "PAD645")
    vig_lazer = _bloco_minutos_paq(df, "PAQ650", "PAQ655", "PAD660")
    mod_lazer = _bloco_minutos_paq(df, "PAQ665", "PAQ670", "PAD675")

    # Soma preservando NaN apenas se TODOS os blocos forem nulos
    todos_blocos_nulos = (
        vig_trab.isna() & mod_trab.isna() & desloc.isna() & vig_lazer.isna() & mod_lazer.isna()
    )
    df["min_vig_semana"] = vig_trab.fillna(0) + vig_lazer.fillna(0)
    df["min_mod_semana"] = mod_trab.fillna(0) + mod_lazer.fillna(0) + desloc.fillna(0)
    df.loc[todos_blocos_nulos, ["min_vig_semana", "min_mod_semana"]] = np.nan

    df["met_min_semana"] = 8.0 * df["min_vig_semana"] + 4.0 * df["min_mod_semana"]
    # Limite superior plausível para evitar distorção de autorrelato extremo
    df["met_min_semana"] = df["met_min_semana"].clip(upper=12000.0)

    df["cumpre_oms_150"] = np.where(
        df["met_min_semana"].isna(), np.nan, (df["met_min_semana"] >= 600.0).astype(float)
    )
    df["sedentarismo_alto"] = np.where(
        df["minutos_sentado"].isna(), np.nan, (df["minutos_sentado"] >= 480.0).astype(float)
    )

    # Perfil de movimento (4 classes — Quadro 9)
    condicoes_mov = [
        (df["cumpre_oms_150"] == 1) & (df["sedentarismo_alto"] == 0),
        (df["cumpre_oms_150"] == 1) & (df["sedentarismo_alto"] == 1),
        (df["cumpre_oms_150"] == 0) & (df["sedentarismo_alto"] == 0),
        (df["cumpre_oms_150"] == 0) & (df["sedentarismo_alto"] == 1),
    ]
    escolhas_mov = [
        "Ativo & Pouco Sentado",
        "Ativo & Muito Sentado",
        "Inativo & Pouco Sentado",
        "Inativo & Muito Sentado",
    ]
    df["perfil_movimento"] = np.select(condicoes_mov, escolhas_mov, default="Desconhecido")

    # -------------------------------------------------------------------------
    # 4.6 Cofatores Clínicos de Rotina Permitidos (Quadro 11)
    # -------------------------------------------------------------------------
    df["faixa_imc"] = pd.cut(
        df["imc"],
        bins=[0, 18.5, 25.0, 30.0, 100.0],
        right=False,
        labels=["Baixo Peso", "Adequado", "Sobrepeso", "Obesidade"],
    ).astype(str)

    df["razao_cintura_estatura"] = df["cintura_cm"] / df["altura_cm"]

    df["pressao_alta"] = np.where(
        df["pas_mmhg"].isna() & df["pad_mmhg"].isna(),
        np.nan,
        ((df["pas_mmhg"] >= 140.0) | (df["pad_mmhg"] >= 90.0)).astype(float),
    )

    df["razao_ct_hdl"] = df["colesterol_total"] / df["hdl"].replace(0, np.nan)

    # Histórico familiar de diabetes (MCQ300C: 1 = Sim, 2 = Não)
    df["historico_familiar_diabetes"] = np.where(
        df["MCQ300C"].isna(),
        np.nan,
        np.where(df["MCQ300C"] == 1, 1.0, 0.0),
    )

    # Tabagismo (cofator exploratório: SMQ020 == 1 -> 1.0, == 2 -> 0.0)
    df["tabagismo_100cig"] = np.where(
        df["SMQ020"].isna(), np.nan, np.where(df["SMQ020"] == 1, 1.0, 0.0)
    )

    # -------------------------------------------------------------------------
    # 4.8 e 4.9 Verificação de Vazamento, Dicionário de Dados e Auditoria de Features
    # -------------------------------------------------------------------------
    intersecao_proibida = set(FEATURES_MODELO_X) & set(VARIAVEIS_BLOQUEADAS_VAZAMENTO)
    assert len(intersecao_proibida) == 0, f"VIOLAÇÃO DE DATA LEAKAGE: {intersecao_proibida}"

    # Salva blocklist formal
    (PROCESSED_DIR / "leakage_blocklist.txt").write_text(
        "# DATA LEAKAGE SHIELD — VARIÁVEIS BLOQUEADAS NO VETOR PREDITOR X (BLOCO 3)\n"
        "# Qualquer coluna abaixo define diretamente o alvo clínico/medicamentoso ou ocorre pós-diagnóstico:\n"
        + "\n".join(VARIAVEIS_BLOQUEADAS_VAZAMENTO)
        + "\n",
        encoding="utf-8",
    )

    # Gera auditoria estatística de cada coluna de X (Seção 4.8 do Bloco 2)
    metadados_features = {
        "idade_anos": ("Demográfico", "contínua", "anos", "Idade do participante (top-coded em 80 anos)"),
        "sexo": ("Demográfico", "categórica binária", "1=M, 2=F", "Sexo biológico para ajuste epidemiológico"),
        "escolaridade_ord": ("Eixo 3 (Social/Território)", "ordinal (1 a 5)", "nível", "Escolaridade adulta (DMDEDUC2)"),
        "razao_renda_pobreza": ("Eixo 3 (Social/Território)", "contínua", "razão (0 a 5)", "Razão entre renda familiar e linha de pobreza federal (INDFMPIR)"),
        "inseguranca_alimentar": ("Eixo 3 (Social/Território)", "binária (0/1)", "indicador", "Presença de insegurança alimentar domiciliar (FSDHH > 1)"),
        "densidade_acucar": ("Eixo 1 (Alimentação)", "contínua", "g/1000 kcal", "Açúcares totais por 1000 kcal ingeridas (DR1TSUGR/DR1TKCAL*1000)"),
        "densidade_fibra": ("Eixo 1 (Alimentação)", "contínua", "g/1000 kcal", "Fibra alimentar por 1000 kcal ingeridas (DR1TFIBE/DR1TKCAL*1000)"),
        "excesso_sodio": ("Eixo 1 (Alimentação)", "binária (0/1)", "indicador", "Ingestão de sódio >= 2300 mg/dia (limiar diretriz CDC/FDA)"),
        "indice_qualidade_dieta": ("Eixo 1 (Alimentação)", "contínua (z-score)", "escore padronizado", "Média de z-scores (+fibra -açúcar -sódio -gordura saturada) ajustada no treino"),
        "refeicao_pronta": ("Eixo 1 (Alimentação)", "contínua discreta", "refeições/sem", "Frequência semanal de refeições preparadas fora de casa / fast-food (DBD895)"),
        "met_min_semana": ("Eixo 2 (Movimento)", "contínua", "MET-min/sem", "Volume semanal de atividade física moderada (4 MET) e vigorosa (8 MET)"),
        "cumpre_oms_150": ("Eixo 2 (Movimento)", "binária (0/1)", "indicador", "Cumprimento da diretriz OMS (>= 600 MET-min/semana ~ 150 min moderados)"),
        "minutos_sentado": ("Eixo 2 (Movimento)", "contínua", "min/dia", "Tempo diário em comportamento sedentário (PAD680)"),
        "sedentarismo_alto": ("Eixo 2 (Movimento)", "binária (0/1)", "indicador", "Tempo sentado >= 480 min/dia (8 horas ou mais)"),
        "imc": ("Cofator Clínico", "contínua", "kg/m²", "Índice de Massa Corporal medido em exame físico (BMXBMI)"),
        "razao_cintura_estatura": ("Cofator Clínico", "contínua", "razão", "Razão circunferência abdominal / estatura (proxy de adiposidade visceral)"),
        "pressao_alta": ("Cofator Clínico", "binária (0/1)", "indicador", "Pressão arterial medida em exame >= 140/90 mmHg (PAS/PAD)"),
        "hdl": ("Cofator Clínico", "contínua", "mg/dL", "Colesterol HDL sérico de rotina (LBDHDD)"),
        "historico_familiar_diabetes": ("Cofator Clínico", "binária (0/1)", "indicador", "Parente próximo de 1º grau com diagnóstico de diabetes (MCQ300C)"),
    }

    linhas_auditoria = []
    linhas_dicionario = []
    for col in FEATURES_MODELO_X:
        eixo, tipo, unidade, desc = metadados_features[col]
        s = df[col]
        n_val = int(s.notna().sum())
        pct_ausente = round(float(s.isna().mean() * 100), 2)
        corr_pearson = round(float(s.corr(df["diabetes"], method="pearson")), 4)
        corr_spearman = round(float(s.corr(df["diabetes"], method="spearman")), 4)
        suspeita_vazamento = abs(corr_pearson) > 0.75 or col in VARIAVEIS_BLOQUEADAS_VAZAMENTO

        assert not suspeita_vazamento, f"Feature {col} apresentou correlação suspeita de vazamento: {corr_pearson}"

        linhas_auditoria.append({
            "feature": col,
            "eixo": eixo,
            "tipo": tipo,
            "unidade": unidade,
            "n_validos": n_val,
            "pct_ausente": pct_ausente,
            "minimo": round(float(s.min()), 3) if n_val > 0 else np.nan,
            "mediana": round(float(s.median()), 3) if n_val > 0 else np.nan,
            "media": round(float(s.mean()), 3) if n_val > 0 else np.nan,
            "maximo": round(float(s.max()), 3) if n_val > 0 else np.nan,
            "corr_pearson_alvo": corr_pearson,
            "corr_spearman_alvo": corr_spearman,
            "flag_vazamento": "NÃO (Auditada)",
        })

        linhas_dicionario.append({
            "nome_analitico": col,
            "papel_no_modelo": "Preditor (X)",
            "eixo_tematico": eixo,
            "tipo_dado": tipo,
            "unidade": unidade,
            "pct_ausente_amostra": pct_ausente,
            "descricao_negocio": desc,
        })

    # Adiciona variáveis de alvo e bloqueadas ao dicionário de dados para transparência
    for col_alvo, desc_alvo in [
        ("diabetes", "Alvo binário (y): 1 se DIQ010==1 ou HbA1c>=6.5% ou Glicemia>=126 mg/dL"),
        ("hba1c", "Glicohemoglobina (%) — usada exclusivamente na definição de y (bloqueada em X)"),
        ("glicemia_jejum", "Glicemia plasmática de jejum (mg/dL) — exclusiva para y (bloqueada em X)"),
        ("diabetes_autorrelato", "Autorrelato diagnóstico prévio (DIQ010) — exclusivo para y (bloqueado em X)"),
        ("triglicerideos", "Triglicerídeos de jejum (mg/dL) — coletada, não modelada (>40% ausente por subamostra)"),
        ("ldl", "Colesterol LDL de jejum (mg/dL) — coletada, não modelada (>40% ausente por subamostra)"),
    ]:
        s = df[col_alvo]
        linhas_dicionario.append({
            "nome_analitico": col_alvo,
            "papel_no_modelo": "Alvo (y)" if col_alvo == "diabetes" else "Bloqueada / Fora de X",
            "eixo_tematico": "Desfecho / Governança",
            "tipo_dado": "contínua/binária",
            "unidade": "variável",
            "pct_ausente_amostra": round(float(s.isna().mean() * 100), 2),
            "descricao_negocio": desc_alvo,
        })

    df_audit = pd.DataFrame(linhas_auditoria)
    df_dict = pd.DataFrame(linhas_dicionario)

    df_audit.to_csv(PROCESSED_DIR / "feature_audit.csv", index=False, encoding="utf-8")
    df_dict.to_csv(PROCESSED_DIR / "data_dictionary.csv", index=False, encoding="utf-8")
    df.to_parquet(PROCESSED_DIR / "analytic.parquet", index=False)
    df.to_csv(PROCESSED_DIR / "analytic.csv", index=False, encoding="utf-8")

    print(
        f"[Features] analytic.parquet gerado ({len(df)} linhas x {df.shape[1]} colunas) | "
        f"19 features de X auditadas com 0% de vazamento."
    )
    return df


if __name__ == "__main__":
    construir_features()
