from __future__ import annotations

import os
from datetime import timedelta

import pandas as pd
from longport.openapi import AdjustType, Config, Period, QuoteContext

from .base import DataSource, FetchRequest


class LongPortSource(DataSource):
    name = "longport"

    def __init__(self) -> None:
        self.app_key = os.getenv("LONGPORT_APP_KEY", "").strip()
        self.app_secret = os.getenv("LONGPORT_APP_SECRET", "").strip()
        self.access_token = os.getenv("LONGPORT_ACCESS_TOKEN", "").strip()

    @staticmethod
    def _to_longport_symbol(symbol: str) -> str:
        s = symbol.strip().upper()
        if "." in s:
            code, market = s.split(".", 1)
            if market == "HK":
                return f"{str(int(code))}.HK"
            return f"{code}.{market}"

        if s.startswith("6"):
            return f"{s}.SH"
        if s.startswith(("0", "3")):
            return f"{s}.SZ"
        return s

    def fetch(self, request: FetchRequest) -> pd.DataFrame:
        if not (self.app_key and self.app_secret and self.access_token):
            raise NotImplementedError(
                "missing LONGPORT_APP_KEY/LONGPORT_APP_SECRET/LONGPORT_ACCESS_TOKEN in .env"
            )

        config = Config(
            app_key=self.app_key,
            app_secret=self.app_secret,
            access_token=self.access_token,
        )
        ctx = QuoteContext(config)
        symbol = self._to_longport_symbol(request.symbol)
        end_date = request.end_date + timedelta(days=1)
        candles = ctx.history_candlesticks_by_date(
            symbol,
            Period.Day,
            AdjustType.NoAdjust,
            request.start_date,
            end_date,
        )
        rows = [
            {
                "date": c.timestamp.date(),
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in candles
        ]
        return self.normalize_columns(pd.DataFrame(rows), request.symbol)
