from __future__ import annotations

import efinance as ef
import pandas as pd

from .base import DataSource, FetchRequest


class EFinanceSource(DataSource):
    name = "efinance"

    def fetch(self, request: FetchRequest) -> pd.DataFrame:
        beg = request.start_date.strftime("%Y%m%d")
        end = request.end_date.strftime("%Y%m%d")
        klt = 101  # daily kline
        stock_code = request.symbol.replace(".HK", "")
        df = ef.stock.get_quote_history(stock_code, beg=beg, end=end, klt=klt)
        return self.normalize_columns(df, request.symbol)
