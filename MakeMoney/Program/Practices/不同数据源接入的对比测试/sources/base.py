from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd


@dataclass
class FetchRequest:
    symbol: str
    start_date: date
    end_date: date
    interval: str = "daily"


class DataSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, request: FetchRequest) -> pd.DataFrame:
        """Return a normalized OHLCV DataFrame."""

    def normalize_columns(self, df: pd.DataFrame, symbol: Optional[str] = None) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "symbol"])

        col_map = {c.lower(): c for c in df.columns}
        expected = {
            "date": ["date", "datetime", "time", "日期", "交易日期"],
            "open": ["open", "开盘", "今开"],
            "high": ["high", "最高"],
            "low": ["low", "最低"],
            "close": ["close", "收盘", "最新价"],
            "volume": ["volume", "vol", "成交量"],
        }

        selected = {}
        for target, aliases in expected.items():
            for alias in aliases:
                key = alias.lower()
                if key in col_map:
                    selected[target] = df[col_map[key]]
                    break

        normalized = pd.DataFrame(selected)
        if "date" not in normalized.columns:
            raise ValueError(f"missing date column, available columns: {list(df.columns)}")

        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
        if symbol:
            normalized["symbol"] = symbol
        return normalized.dropna(subset=["date"]).reset_index(drop=True)
