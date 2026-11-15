"""
Módulo de extração dos microdados públicos do CDC/NCHS NHANES (Ciclo 2017-2018).
Atende às especificações das seções 2.2 e 2.7 da Documentação Técnica do Bloco 2:
- Download dos 16 arquivos XPT originais do ciclo 2017-2018 (sufixo _J)
- Preservação imutável na camada data/raw/nhanes
- Registro do contrato de extração (URL, data/hora, SHA-256, linhas, SEQN únicos)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_NHANES_DIR = ROOT_DIR / "data" / "raw" / "nhanes"
MANIFEST_PATH = ROOT_DIR / "data" / "raw" / "manifest_extracao.json"

CICLO = "2017-2018"
BASE_URLS = [
    "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/",
    f"https://wwwn.cdc.gov/Nchs/Nhanes/{CICLO}/",
]

ARQUIVOS: dict[str, str] = {
    "demo": "DEMO_J.XPT",
    "bmx": "BMX_J.XPT",
    "bpx": "BPX_J.XPT",
    "tchol": "TCHOL_J.XPT",
    "hdl": "HDL_J.XPT",
    "trigly": "TRIGLY_J.XPT",
    "ghb": "GHB_J.XPT",
    "glu": "GLU_J.XPT",
    "diq": "DIQ_J.XPT",
    "dr1tot": "DR1TOT_J.XPT",
    "dbq": "DBQ_J.XPT",
    "paq": "PAQ_J.XPT",
    "smq": "SMQ_J.XPT",
    "alq": "ALQ_J.XPT",
    "mcq": "MCQ_J.XPT",
    "fsq": "FSQ_J.XPT",
}


def calcular_sha256(caminho: Path) -> str:
    """Calcula o hash SHA-256 de um arquivo bruto para auditoria de reprodutibilidade."""
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def baixar_xpt_cdc(arquivo: str, destino_xpt: Path) -> str:
    """Baixa o arquivo XPT oficial do CDC caso ainda não esteja em cache local."""
    if destino_xpt.exists() and destino_xpt.stat().st_size > 1024:
        return f"local_cache:{destino_xpt.name} ({BASE_URLS[0]}{arquivo})"

    erros = []
    for base in BASE_URLS:
        for nome_cand in [arquivo, arquivo.lower(), arquivo.replace(".XPT", ".xpt")]:
            url = base + nome_cand
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "UNEX-MineracaoDados-Bloco3/1.0 (Academic Research)"},
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    conteudo = resp.read()
                    if len(conteudo) > 1024 and b"HEADER RECORD" in conteudo[:256]:
                        destino_xpt.write_bytes(conteudo)
                        return url
            except Exception as exc:  # noqa: BLE001
                erros.append(f"{url}: {exc}")
    raise RuntimeError(f"Falha ao baixar {arquivo} do CDC: {'; '.join(erros)}")


def extrair_nhanes(forcar_download: bool = False) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    """
    Executa a extração dos 16 componentes do NHANES 2017-2018, salva cópia bruta
    em XPT e Parquet e gera o manifesto auditável exigido na seção 2.7 do Bloco 2.
    """
    RAW_NHANES_DIR.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    contratos: list[dict] = []

    for nome, arquivo in ARQUIVOS.items():
        caminho_xpt = RAW_NHANES_DIR / arquivo
        caminho_parquet = RAW_NHANES_DIR / f"{nome}.parquet"

        if forcar_download and caminho_xpt.exists():
            caminho_xpt.unlink()

        url_usada = baixar_xpt_cdc(arquivo, caminho_xpt)
        df = pd.read_sas(caminho_xpt, format="xport")
        # Garante que SEQN seja inteiro para junção exata
        if "SEQN" in df.columns:
            df["SEQN"] = df["SEQN"].round().astype("int64")

        df.to_parquet(caminho_parquet, index=False)
        frames[nome] = df

        contrato = {
            "componente": nome,
            "arquivo_original": arquivo,
            "url_origem": url_usada,
            "data_hora_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "sha256_bruto": calcular_sha256(caminho_xpt),
            "tamanho_bytes": caminho_xpt.stat().st_size,
            "n_linhas": int(len(df)),
            "n_colunas": int(df.shape[1]),
            "n_seqn_unicos": int(df["SEQN"].nunique()) if "SEQN" in df.columns else 0,
            "ciclo": CICLO,
        }
        contratos.append(contrato)
        print(
            f"[NHANES] {arquivo:<12} | linhas={contrato['n_linhas']:>5} "
            f"| SEQN={contrato['n_seqn_unicos']:>5} | sha256={contrato['sha256_bruto'][:12]}..."
        )

    # Atualiza manifesto de extração
    manifesto_atual = {}
    if MANIFEST_PATH.exists():
        try:
            manifesto_atual = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            manifesto_atual = {}

    manifesto_atual["nhanes_2017_2018"] = contratos
    MANIFEST_PATH.write_text(json.dumps(manifesto_atual, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(contratos).to_csv(RAW_NHANES_DIR / "contrato_extracao_nhanes.csv", index=False)

    return frames, contratos


def carregar_nhanes_local() -> dict[str, pd.DataFrame]:
    """Carrega os arquivos Parquet já extraídos em data/raw/nhanes."""
    frames: dict[str, pd.DataFrame] = {}
    for nome in ARQUIVOS:
        p = RAW_NHANES_DIR / f"{nome}.parquet"
        if not p.exists():
            frames, _ = extrair_nhanes()
            return frames
        frames[nome] = pd.read_parquet(p)
    return frames


if __name__ == "__main__":
    extrair_nhanes()
