from __future__ import annotations

from datetime import date

import akshare as ak
import pandas as pd

from .base import DataSource, FetchRequest


class AkShareSource(DataSource):
    name = "akshare"

    def fetch(self, request: FetchRequest) -> pd.DataFrame:
        start = request.start_date.strftime("%Y%m%d")
        end = request.end_date.strftime("%Y%m%d")

        if request.symbol.endswith(".HK"):
            symbol = request.symbol.replace(".HK", "")
            df = ak.stock_hk_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="",
            )
        else:
            symbol = request.symbol
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            )
        return self.normalize_columns(df, request.symbol)
