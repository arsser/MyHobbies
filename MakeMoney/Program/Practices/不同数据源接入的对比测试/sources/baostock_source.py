from __future__ import annotations

import baostock as bs
import pandas as pd

from .base import DataSource, FetchRequest


class BaoStockSource(DataSource):
    name = "baostock"

    def fetch(self, request: FetchRequest) -> pd.DataFrame:
        if request.symbol.upper().endswith(".HK"):
            raise NotImplementedError("baostock does not support HK symbols in this benchmark")

        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"BaoStock login failed: {lg.error_msg}")

        try:
            symbol = request.symbol.lower()
            if not symbol.startswith(("sh.", "sz.", "hk.")):
                symbol = f"sh.{symbol}" if symbol.startswith("6") else f"sz.{symbol}"
            rs = bs.query_history_k_data_plus(
                code=symbol,
                fields="date,open,high,low,close,volume",
                start_date=request.start_date.isoformat(),
                end_date=request.end_date.isoformat(),
                frequency="d",
                adjustflag="2",
            )
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            if rs.error_code != "0":
                raise RuntimeError(f"BaoStock query failed: {rs.error_msg}")
            df = pd.DataFrame(rows, columns=rs.fields)
            return self.normalize_columns(df, request.symbol)
        finally:
            bs.logout()
