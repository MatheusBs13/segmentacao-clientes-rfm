"""Funções para construir features RFM e uma segmentação por regras (baseline)."""

import numpy as np
import pandas as pd


def build_rfm(df: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Calcula Recência, Frequência e Valor Monetário por cliente.

    Espera as colunas: CustomerID, Invoice, InvoiceDate, Revenue.

    - Recency:   dias entre a última compra do cliente e a data de referência
    - Frequency: número de notas fiscais distintas
    - Monetary:  soma da receita do cliente

    Se `snapshot_date` não for informada, usa o dia seguinte à última compra da base.
    """
    df = df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    if snapshot_date is None:
        snapshot_date = df["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

    grouped = df.groupby("CustomerID")
    rfm = pd.DataFrame(
        {
            "Recency": (snapshot_date - grouped["InvoiceDate"].max()).dt.days,
            "Frequency": grouped["Invoice"].nunique(),
            "Monetary": grouped["Revenue"].sum(),
        }
    )
    return rfm


def rfm_scores(rfm: pd.DataFrame, bins: int = 5) -> pd.DataFrame:
    """Notas de 1 a `bins` para cada dimensão (quanto maior, melhor).

    Usa o ranking antes do corte em quantis para evitar erro quando há muitos
    valores repetidos (comum em Frequency).
    """
    out = rfm.copy()
    labels = list(range(1, bins + 1))
    out["R"] = pd.qcut(out["Recency"].rank(method="first"), bins, labels=labels[::-1]).astype(int)
    out["F"] = pd.qcut(out["Frequency"].rank(method="first"), bins, labels=labels).astype(int)
    out["M"] = pd.qcut(out["Monetary"].rank(method="first"), bins, labels=labels).astype(int)
    out["RFM_score"] = out["R"] + out["F"] + out["M"]
    return out


def rule_based_segment(scores: pd.DataFrame) -> pd.Series:
    """Segmentação clássica por regras, usada como baseline para comparar com a clusterização."""
    r, f = scores["R"], scores["F"]
    condicoes = [
        (r >= 4) & (f >= 4),
        (r >= 3) & (f >= 3),
        (r >= 4) & (f <= 2),
        (r <= 2) & (f >= 3),
        (r <= 2) & (f <= 2),
    ]
    nomes = ["Campeões", "Leais", "Novos", "Em risco", "Hibernando"]
    return pd.Series(np.select(condicoes, nomes, default="Potenciais"), index=scores.index, name="Segmento_regra")
