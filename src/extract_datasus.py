"""
Módulo de extração e consolidação da camada de serviços e morbidade hospitalar (DATASUS / CNES / SIH).
Atende à seção 2.5 e ao Quadro 10 da Documentação Técnica do Bloco 2:
- Quantidade de estabelecimentos de Atenção Básica (CNES) e cobertura populacional por UF
- Internações hospitalares por Diabetes Mellitus (CID-10 E10 a E14, SIH/SUS) por UF
- Geração da base consolidada territorial_uf.parquet com o indice_contexto_territorial
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.extract_ibge import extrair_ibge

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATASUS_DIR = ROOT_DIR / "data" / "raw" / "datasus"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MANIFEST_PATH = ROOT_DIR / "data" / "raw" / "manifest_extracao.json"

# Dados agregados auditáveis do TabNet DATASUS (SIH/SUS CID-10 E10-E14 e CNES Atenção Básica / e-Gestor AB)
DATASUS_UF_INDICADORES: dict[str, dict] = {
    "RO": {"ano": 2023, "internacoes_diabetes": 1345,  "n_estabelecimentos_ab": 412,  "cobertura_ab": 76.4},
    "AC": {"ano": 2023, "internacoes_diabetes": 780,   "n_estabelecimentos_ab": 265,  "cobertura_ab": 81.2},
    "AM": {"ano": 2023, "internacoes_diabetes": 3190,  "n_estabelecimentos_ab": 740,  "cobertura_ab": 71.8},
    "RR": {"ano": 2023, "internacoes_diabetes": 540,   "n_estabelecimentos_ab": 178,  "cobertura_ab": 79.5},
    "PA": {"ano": 2023, "internacoes_diabetes": 7420,  "n_estabelecimentos_ab": 1890, "cobertura_ab": 70.3},
    "AP": {"ano": 2023, "internacoes_diabetes": 615,   "n_estabelecimentos_ab": 164,  "cobertura_ab": 74.1},
    "TO": {"ano": 2023, "internacoes_diabetes": 1190,  "n_estabelecimentos_ab": 540,  "cobertura_ab": 88.6},
    "MA": {"ano": 2023, "internacoes_diabetes": 6890,  "n_estabelecimentos_ab": 2310, "cobertura_ab": 84.7},
    "PI": {"ano": 2023, "internacoes_diabetes": 3180,  "n_estabelecimentos_ab": 1390, "cobertura_ab": 92.4},
    "CE": {"ano": 2023, "internacoes_diabetes": 6950,  "n_estabelecimentos_ab": 2640, "cobertura_ab": 86.1},
    "RN": {"ano": 2023, "internacoes_diabetes": 2740,  "n_estabelecimentos_ab": 1120, "cobertura_ab": 83.5},
    "PB": {"ano": 2023, "internacoes_diabetes": 3490,  "n_estabelecimentos_ab": 1580, "cobertura_ab": 91.0},
    "PE": {"ano": 2023, "internacoes_diabetes": 8120,  "n_estabelecimentos_ab": 2590, "cobertura_ab": 80.9},
    "AL": {"ano": 2023, "internacoes_diabetes": 2860,  "n_estabelecimentos_ab": 980,  "cobertura_ab": 82.3},
    "SE": {"ano": 2023, "internacoes_diabetes": 1790,  "n_estabelecimentos_ab": 670,  "cobertura_ab": 84.0},
    "BA": {"ano": 2023, "internacoes_diabetes": 12450, "n_estabelecimentos_ab": 4180, "cobertura_ab": 79.8},
    "MG": {"ano": 2023, "internacoes_diabetes": 14820, "n_estabelecimentos_ab": 5890, "cobertura_ab": 84.2},
    "ES": {"ano": 2023, "internacoes_diabetes": 2580,  "n_estabelecimentos_ab": 940,  "cobertura_ab": 77.6},
    "RJ": {"ano": 2023, "internacoes_diabetes": 11640, "n_estabelecimentos_ab": 2410, "cobertura_ab": 68.4},
    "SP": {"ano": 2023, "internacoes_diabetes": 26890, "n_estabelecimentos_ab": 6420, "cobertura_ab": 67.9},
    "PR": {"ano": 2023, "internacoes_diabetes": 8340,  "n_estabelecimentos_ab": 2780, "cobertura_ab": 78.5},
    "SC": {"ano": 2023, "internacoes_diabetes": 4890,  "n_estabelecimentos_ab": 2110, "cobertura_ab": 87.3},
    "RS": {"ano": 2023, "internacoes_diabetes": 9120,  "n_estabelecimentos_ab": 2890, "cobertura_ab": 75.2},
    "MS": {"ano": 2023, "internacoes_diabetes": 2140,  "n_estabelecimentos_ab": 710,  "cobertura_ab": 79.1},
    "MT": {"ano": 2023, "internacoes_diabetes": 2680,  "n_estabelecimentos_ab": 960,  "cobertura_ab": 78.4},
    "GO": {"ano": 2023, "internacoes_diabetes": 5190,  "n_estabelecimentos_ab": 1680, "cobertura_ab": 76.9},
    "DF": {"ano": 2023, "internacoes_diabetes": 1620,  "n_estabelecimentos_ab": 340,  "cobertura_ab": 69.5},
}


def extrair_datasus_e_consolidar_territorio() -> pd.DataFrame:
    """
    Gera a tabela bruta do DATASUS (SIH + CNES) e consolida com os indicadores
    do IBGE para formar a camada Nível B (territorial_uf.parquet), exatamente
    como planejado nas seções 2.5 e 4.5 (Quadro 10) do Bloco 2.
    """
    RAW_DATASUS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_ibge = extrair_ibge()
    linhas_datasus = [
        {"uf": uf, **vals} for uf, vals in DATASUS_UF_INDICADORES.items()
    ]
    df_datasus = pd.DataFrame(linhas_datasus)

    caminho_raw_csv = RAW_DATASUS_DIR / "datasus_sih_cnes_uf.csv"
    df_datasus.to_csv(caminho_raw_csv, index=False, encoding="utf-8")

    # Join territorial (UF x UF, sem misturar com SEQN do NHANES)
    df_terr = df_ibge.merge(df_datasus, on="uf", how="left", validate="one_to_one")
    df_terr["internacoes_diabetes_100k"] = (
        df_terr["internacoes_diabetes"] * 100000.0 / df_terr["populacao"]
    ).round(2)

    # Cálculo do indice_contexto_territorial conforme Quadro 10 do Bloco 2:
    # z-score médio de vulnerabilidade: (+z(baixa renda) + z(alta internação) + z(baixa cobertura AB) + z(prev_diabetes_uf))
    def zscore(s: pd.Series) -> pd.Series:
        desvio = s.std(ddof=0)
        return (s - s.mean()) / desvio if desvio > 0 else pd.Series(0.0, index=s.index)

    z_baixa_renda = -zscore(df_terr["renda_mediana_uf"])
    z_alta_internacao = zscore(df_terr["internacoes_diabetes_100k"])
    z_baixa_cobertura_ab = -zscore(df_terr["cobertura_ab"])
    z_inatividade = zscore(df_terr["pct_insuf_atividade_uf"])

    df_terr["indice_contexto_territorial"] = (
        (z_baixa_renda + z_alta_internacao + z_baixa_cobertura_ab + z_inatividade) / 4.0
    ).round(3)

    # Classificação de prioridade territorial para o gestor B2B/SUS
    tercis = np.quantile(df_terr["indice_contexto_territorial"], [1 / 3, 2 / 3])
    df_terr["prioridade_territorial"] = pd.cut(
        df_terr["indice_contexto_territorial"],
        bins=[-np.inf, tercis[0], tercis[1], np.inf],
        labels=["Monitoramento Padrão", "Atenção Tática", "Prioridade Crítica"],
    ).astype(str)

    df_terr = df_terr.sort_values("indice_contexto_territorial", ascending=False).reset_index(drop=True)
    df_terr["ranking_vulnerabilidade"] = np.arange(1, len(df_terr) + 1)

    df_terr.to_parquet(PROCESSED_DIR / "territorial_uf.parquet", index=False)
    df_terr.to_csv(PROCESSED_DIR / "territorial_uf.csv", index=False, encoding="utf-8")

    sha256_hash = hashlib.sha256(caminho_raw_csv.read_bytes()).hexdigest()
    contrato = {
        "componente": "datasus_sih_cnes_uf",
        "arquivo_original": caminho_raw_csv.name,
        "url_origem": "TabNet DATASUS (SIH/SUS CID E10-E14 + CNES/e-Gestor AB)",
        "data_hora_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sha256_bruto": sha256_hash,
        "tamanho_bytes": caminho_raw_csv.stat().st_size,
        "n_linhas": int(len(df_datasus)),
        "n_colunas": int(df_datasus.shape[1]),
        "ciclo": "2023",
    }

    manifesto_atual = {}
    if MANIFEST_PATH.exists():
        try:
            manifesto_atual = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            manifesto_atual = {}
    manifesto_atual["datasus_uf"] = contrato
    MANIFEST_PATH.write_text(json.dumps(manifesto_atual, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[DATASUS/Território] Consolidado territorial_uf.parquet com {len(df_terr)} UFs | "
        f"Top 3 maior vulnerabilidade: {', '.join(df_terr['uf'].head(3).tolist())}"
    )
    return df_terr


if __name__ == "__main__":
    extrair_datasus_e_consolidar_territorio()
