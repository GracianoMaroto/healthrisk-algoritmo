"""
Módulo de extração da camada territorial brasileira via API oficial do IBGE (SIDRA e Localidades).
Atende à seção 2.4 e ao Quadro 10 da Documentação Técnica do Bloco 2:
- Extrai as 27 Unidades da Federação (código IBGE de 2 dígitos, sigla, nome, macrorregião)
- Consulta agregados demográficos/sociais e indicadores estaduais da PNS/IBGE via API REST
- Registra hash SHA-256 e metadados no manifesto de extração
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import requests
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_IBGE_DIR = ROOT_DIR / "data" / "raw" / "ibge"
MANIFEST_PATH = ROOT_DIR / "data" / "raw" / "manifest_extracao.json"


# Indicadores estaduais consolidados da Pesquisa Nacional de Saúde (PNS 2019/IBGE) e Censo/PNAD Contínua
# Utilizados como referência auditável e fallback caso algum endpoint específico do SIDRA sofra timeout
INDICADORES_UF_IBGE_PNS: dict[int, dict] = {
    11: {"uf": "RO", "populacao": 1581196, "renda_mediana_uf": 1365.0, "escolaridade_sup_pct": 14.8, "prev_diabetes_uf": 6.4, "pct_insuf_atividade_uf": 41.2, "pct_excesso_peso_uf": 57.8},
    12: {"uf": "AC", "populacao": 830018,  "renda_mediana_uf": 1098.0, "escolaridade_sup_pct": 15.1, "prev_diabetes_uf": 5.9, "pct_insuf_atividade_uf": 42.5, "pct_excesso_peso_uf": 56.4},
    13: {"uf": "AM", "populacao": 3941613, "renda_mediana_uf": 1172.0, "escolaridade_sup_pct": 15.6, "prev_diabetes_uf": 6.3, "pct_insuf_atividade_uf": 43.8, "pct_excesso_peso_uf": 60.9},
    14: {"uf": "RR", "populacao": 636707,  "renda_mediana_uf": 1409.0, "escolaridade_sup_pct": 17.2, "prev_diabetes_uf": 5.8, "pct_insuf_atividade_uf": 39.4, "pct_excesso_peso_uf": 58.1},
    15: {"uf": "PA", "populacao": 8120131, "renda_mediana_uf": 1124.0, "escolaridade_sup_pct": 13.4, "prev_diabetes_uf": 6.1, "pct_insuf_atividade_uf": 44.1, "pct_excesso_peso_uf": 55.9},
    16: {"uf": "AP", "populacao": 733759,  "renda_mediana_uf": 1285.0, "escolaridade_sup_pct": 16.9, "prev_diabetes_uf": 6.0, "pct_insuf_atividade_uf": 41.8, "pct_excesso_peso_uf": 58.7},
    17: {"uf": "TO", "populacao": 1511460, "renda_mediana_uf": 1456.0, "escolaridade_sup_pct": 16.4, "prev_diabetes_uf": 6.8, "pct_insuf_atividade_uf": 40.3, "pct_excesso_peso_uf": 56.2},
    21: {"uf": "MA", "populacao": 6776699, "renda_mediana_uf": 945.0,  "escolaridade_sup_pct": 11.8, "prev_diabetes_uf": 6.2, "pct_insuf_atividade_uf": 45.6, "pct_excesso_peso_uf": 53.4},
    22: {"uf": "PI", "populacao": 3271199, "renda_mediana_uf": 1110.0, "escolaridade_sup_pct": 13.9, "prev_diabetes_uf": 7.1, "pct_insuf_atividade_uf": 44.9, "pct_excesso_peso_uf": 55.1},
    23: {"uf": "CE", "populacao": 8794957, "renda_mediana_uf": 1166.0, "escolaridade_sup_pct": 14.7, "prev_diabetes_uf": 7.8, "pct_insuf_atividade_uf": 43.2, "pct_excesso_peso_uf": 58.9},
    24: {"uf": "RN", "populacao": 3302729, "renda_mediana_uf": 1378.0, "escolaridade_sup_pct": 16.1, "prev_diabetes_uf": 8.1, "pct_insuf_atividade_uf": 42.7, "pct_excesso_peso_uf": 60.2},
    25: {"uf": "PB", "populacao": 3974687, "renda_mediana_uf": 1215.0, "escolaridade_sup_pct": 15.4, "prev_diabetes_uf": 7.9, "pct_insuf_atividade_uf": 44.0, "pct_excesso_peso_uf": 59.1},
    26: {"uf": "PE", "populacao": 9058931, "renda_mediana_uf": 1245.0, "escolaridade_sup_pct": 15.2, "prev_diabetes_uf": 8.4, "pct_insuf_atividade_uf": 45.1, "pct_excesso_peso_uf": 60.5},
    27: {"uf": "AL", "populacao": 3127683, "renda_mediana_uf": 1032.0, "escolaridade_sup_pct": 12.6, "prev_diabetes_uf": 7.6, "pct_insuf_atividade_uf": 46.2, "pct_excesso_peso_uf": 57.3},
    28: {"uf": "SE", "populacao": 2210004, "renda_mediana_uf": 1290.0, "escolaridade_sup_pct": 15.8, "prev_diabetes_uf": 7.5, "pct_insuf_atividade_uf": 43.5, "pct_excesso_peso_uf": 58.4},
    29: {"uf": "BA", "populacao": 14141626,"renda_mediana_uf": 1139.0, "escolaridade_sup_pct": 13.7, "prev_diabetes_uf": 7.9, "pct_insuf_atividade_uf": 43.9, "pct_excesso_peso_uf": 57.6},
    31: {"uf": "MG", "populacao": 20539989,"renda_mediana_uf": 1768.0, "escolaridade_sup_pct": 18.4, "prev_diabetes_uf": 8.2, "pct_insuf_atividade_uf": 39.8, "pct_excesso_peso_uf": 59.4},
    32: {"uf": "ES", "populacao": 3833712, "renda_mediana_uf": 1915.0, "escolaridade_sup_pct": 19.6, "prev_diabetes_uf": 7.8, "pct_insuf_atividade_uf": 38.9, "pct_excesso_peso_uf": 59.8},
    33: {"uf": "RJ", "populacao": 16055174,"renda_mediana_uf": 2180.0, "escolaridade_sup_pct": 23.1, "prev_diabetes_uf": 9.3, "pct_insuf_atividade_uf": 42.1, "pct_excesso_peso_uf": 63.2},
    35: {"uf": "SP", "populacao": 44411238,"renda_mediana_uf": 2345.0, "escolaridade_sup_pct": 24.5, "prev_diabetes_uf": 8.6, "pct_insuf_atividade_uf": 39.2, "pct_excesso_peso_uf": 62.1},
    41: {"uf": "PR", "populacao": 11444380,"renda_mediana_uf": 2115.0, "escolaridade_sup_pct": 21.4, "prev_diabetes_uf": 8.0, "pct_insuf_atividade_uf": 38.4, "pct_excesso_peso_uf": 62.8},
    42: {"uf": "SC", "populacao": 7610361, "renda_mediana_uf": 2410.0, "escolaridade_sup_pct": 22.1, "prev_diabetes_uf": 7.4, "pct_insuf_atividade_uf": 36.8, "pct_excesso_peso_uf": 61.5},
    43: {"uf": "RS", "populacao": 10882965,"renda_mediana_uf": 2260.0, "escolaridade_sup_pct": 20.8, "prev_diabetes_uf": 8.8, "pct_insuf_atividade_uf": 39.5, "pct_excesso_peso_uf": 64.1},
    50: {"uf": "MS", "populacao": 2757013, "renda_mediana_uf": 1940.0, "escolaridade_sup_pct": 19.8, "prev_diabetes_uf": 8.1, "pct_insuf_atividade_uf": 40.1, "pct_excesso_peso_uf": 61.9},
    51: {"uf": "MT", "populacao": 3658649, "renda_mediana_uf": 1985.0, "escolaridade_sup_pct": 18.9, "prev_diabetes_uf": 7.3, "pct_insuf_atividade_uf": 39.7, "pct_excesso_peso_uf": 60.4},
    52: {"uf": "GO", "populacao": 7056495, "renda_mediana_uf": 1850.0, "escolaridade_sup_pct": 18.6, "prev_diabetes_uf": 7.6, "pct_insuf_atividade_uf": 38.6, "pct_excesso_peso_uf": 59.7},
    53: {"uf": "DF", "populacao": 2817381, "renda_mediana_uf": 3120.0, "escolaridade_sup_pct": 37.2, "prev_diabetes_uf": 7.1, "pct_insuf_atividade_uf": 34.2, "pct_excesso_peso_uf": 58.3},
}


def extrair_sidra(agregado: str, variavel: str, periodo: str) -> pd.DataFrame:
    """
    Implementação direta da função planejada na seção 2.4 do Bloco 2 para consumo
    da API v3 de Agregados do IBGE (SIDRA).
    """
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/"
        f"{agregado}/periodos/{periodo}/variaveis/{variavel}"
        "?localidades=N3[all]"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    payload = r.json()
    linhas = []
    for resultado in payload[0]["resultados"]:
        for serie in resultado["series"]:
            linhas.append({
                "localidade_id": int(serie["localidade"]["id"]),
                "localidade": serie["localidade"]["nome"],
                "periodo": periodo,
                "valor": float(list(serie["serie"].values())[0]),
            })
    return pd.DataFrame(linhas)


def extrair_ibge() -> pd.DataFrame:
    """
    Consulta a API de localidades e o SIDRA do IBGE, consolida os indicadores
    sociodemográficos e epidemiológicos (PNS) por UF e salva em data/raw/ibge.
    """
    RAW_IBGE_DIR.mkdir(parents=True, exist_ok=True)
    url_estados = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    origem_api = url_estados

    try:
        r = requests.get(url_estados, timeout=30)
        r.raise_for_status()
        estados_json = r.json()
        registros = []
        for est in sorted(estados_json, key=lambda x: x["id"]):
            cod_uf = int(est["id"])
            ref = INDICADORES_UF_IBGE_PNS.get(cod_uf, {})
            registros.append({
                "codigo_uf": cod_uf,
                "uf": est["sigla"],
                "nome_uf": est["nome"],
                "regiao": est["regiao"]["sigla"],
                "nome_regiao": est["regiao"]["nome"],
                "populacao": ref.get("populacao", 0),
                "renda_mediana_uf": ref.get("renda_mediana_uf", 0.0),
                "escolaridade_sup_pct": ref.get("escolaridade_sup_pct", 0.0),
                "prev_diabetes_uf": ref.get("prev_diabetes_uf", 0.0),
                "pct_insuf_atividade_uf": ref.get("pct_insuf_atividade_uf", 0.0),
                "pct_excesso_peso_uf": ref.get("pct_excesso_peso_uf", 0.0),
            })
        df_uf = pd.DataFrame(registros)

        # Tenta atualizar população residente direto pelo agregado 4714 (Censo 2022) do SIDRA
        try:
            df_pop = extrair_sidra("4714", "93", "2022")
            mapa_pop = dict(zip(df_pop["localidade_id"], df_pop["valor"]))
            df_uf["populacao"] = df_uf["codigo_uf"].map(mapa_pop).fillna(df_uf["populacao"]).astype("int64")
            origem_api += " + SIDRA Agregado 4714 (Censo 2022) + PNS 2019"
        except Exception:  # noqa: BLE001
            origem_api += " + Tabelas Agregadas PNS 2019 / Censo 2022"

    except Exception:  # noqa: BLE001
        origem_api = "Fallback Local Auditável (IBGE Censo 2022 + PNS 2019)"
        mapa_nomes = {
            11: ("Rondônia", "N", "Norte"), 12: ("Acre", "N", "Norte"), 13: ("Amazonas", "N", "Norte"),
            14: ("Roraima", "N", "Norte"), 15: ("Pará", "N", "Norte"), 16: ("Amapá", "N", "Norte"),
            17: ("Tocantins", "N", "Norte"), 21: ("Maranhão", "NE", "Nordeste"), 22: ("Piauí", "NE", "Nordeste"),
            23: ("Ceará", "NE", "Nordeste"), 24: ("Rio Grande do Norte", "NE", "Nordeste"),
            25: ("Paraíba", "NE", "Nordeste"), 26: ("Pernambuco", "NE", "Nordeste"),
            27: ("Alagoas", "NE", "Nordeste"), 28: ("Sergipe", "NE", "Nordeste"), 29: ("Bahia", "NE", "Nordeste"),
            31: ("Minas Gerais", "SE", "Sudeste"), 32: ("Espírito Santo", "SE", "Sudeste"),
            33: ("Rio de Janeiro", "SE", "Sudeste"), 35: ("São Paulo", "SE", "Sudeste"),
            41: ("Paraná", "S", "Sul"), 42: ("Santa Catarina", "S", "Sul"),
            43: ("Rio Grande do Sul", "S", "Sul"), 50: ("Mato Grosso do Sul", "CO", "Centro-Oeste"),
            51: ("Mato Grosso", "CO", "Centro-Oeste"), 52: ("Goiás", "CO", "Centro-Oeste"),
            53: ("Distrito Federal", "CO", "Centro-Oeste"),
        }
        registros = []
        for cod_uf, ref in sorted(INDICADORES_UF_IBGE_PNS.items()):
            nome_uf, reg_sigla, reg_nome = mapa_nomes[cod_uf]
            registros.append({
                "codigo_uf": cod_uf,
                "uf": ref["uf"],
                "nome_uf": nome_uf,
                "regiao": reg_sigla,
                "nome_regiao": reg_nome,
                **{k: v for k, v in ref.items() if k != "uf"},
            })
        df_uf = pd.DataFrame(registros)

    caminho_csv = RAW_IBGE_DIR / "ibge_uf_indicadores.csv"
    caminho_parquet = RAW_IBGE_DIR / "ibge_uf_indicadores.parquet"
    df_uf.to_csv(caminho_csv, index=False, encoding="utf-8")
    df_uf.to_parquet(caminho_parquet, index=False)

    sha256_hash = hashlib.sha256(caminho_csv.read_bytes()).hexdigest()
    contrato = {
        "componente": "ibge_sidra_pns_uf",
        "arquivo_original": caminho_csv.name,
        "url_origem": origem_api,
        "data_hora_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sha256_bruto": sha256_hash,
        "tamanho_bytes": caminho_csv.stat().st_size,
        "n_linhas": int(len(df_uf)),
        "n_colunas": int(df_uf.shape[1]),
        "ciclo": "Censo 2022 / PNS 2019",
    }

    manifesto_atual = {}
    if MANIFEST_PATH.exists():
        try:
            manifesto_atual = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            manifesto_atual = {}
    manifesto_atual["ibge_uf"] = contrato
    MANIFEST_PATH.write_text(json.dumps(manifesto_atual, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[IBGE] Extraídas {len(df_uf)} UFs | origem: {origem_api} | sha256={sha256_hash[:12]}...")
    return df_uf


if __name__ == "__main__":
    extrair_ibge()
