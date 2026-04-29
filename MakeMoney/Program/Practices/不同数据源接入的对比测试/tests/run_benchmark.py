from __future__ import annotations

import csv
import os
import random
import socket
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from statistics import mean
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parents[2] / ".env")

from sources import AkShareSource, BaoStockSource, EFinanceSource, LongPortSource
from sources.base import FetchRequest

REPORT_DIR = ROOT / "reports"
RAW_CSV = REPORT_DIR / "raw_metrics.csv"
SUMMARY_CSV = REPORT_DIR / "summary_metrics.csv"
REPORT_MD = REPORT_DIR / "report.md"

# ====== 运行配置（可在脚本开头直接修改）======
# 可选值: "akshare", "efinance", "baostock", "longport"
SELECTED_SOURCE_NAMES = [
    #"akshare",
    #"efinance",
    "baostock",
    "longport",
]
SYMBOLS = ["600036", "00700.HK"]
MAX_ATTEMPTS = 1
THROTTLE_SECONDS = (1.0, 2.0)  # 每次请求后的降频区间（秒）


def log(message: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}")


@dataclass
class Metric:
    source: str
    symbol: str
    ok: bool
    elapsed_ms: float
    row_count: int
    null_rate: float
    skipped: bool = False
    error: str = ""


def run_env_precheck() -> Dict[str, str]:
    targets = [
        ("eastmoney_main", "push2his.eastmoney.com"),
        ("eastmoney_hk", "33.push2his.eastmoney.com"),
    ]
    results: Dict[str, str] = {}

    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]
    enabled_proxies = [k for k in proxy_keys if os.getenv(k)]
    results["proxy"] = ",".join(enabled_proxies) if enabled_proxies else "none"

    for key, host in targets:
        try:
            socket.gethostbyname(host)
            results[f"dns_{key}"] = "ok"
        except OSError as exc:
            results[f"dns_{key}"] = f"fail: {exc}"

        try:
            with socket.create_connection((host, 443), timeout=3):
                results[f"tcp_{key}"] = "ok"
        except OSError as exc:
            results[f"tcp_{key}"] = f"fail: {exc}"

        try:
            req = urllib.request.Request(f"https://{host}", method="HEAD")
            with urllib.request.urlopen(req, timeout=5):
                results[f"https_{key}"] = "ok"
        except Exception as exc:  # noqa: BLE001
            results[f"https_{key}"] = f"fail: {exc}"
    return results


def calc_null_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 1.0
    return float(df.isna().sum().sum() / (df.shape[0] * df.shape[1]))


def run_single(source, symbol: str, start_date: date, end_date: date) -> Metric:
    t0 = time.perf_counter()
    req = FetchRequest(symbol=symbol, start_date=start_date, end_date=end_date)
    last_error = ""
    log(f"[START] source={source.name}, symbol={symbol}, range={start_date}~{end_date}")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            log(f"[TRY] source={source.name}, symbol={symbol}, attempt={attempt}/{MAX_ATTEMPTS}")
            df = source.fetch(req)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            log(
                f"[OK] source={source.name}, symbol={symbol}, rows={len(df)}, "
                f"elapsed_ms={elapsed_ms:.2f}, null_rate={calc_null_rate(df):.4f}"
            )
            return Metric(
                source=source.name,
                symbol=symbol,
                ok=not df.empty,
                elapsed_ms=elapsed_ms,
                row_count=len(df),
                null_rate=calc_null_rate(df),
            )
        except NotImplementedError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            log(
                f"[SKIP] source={source.name}, symbol={symbol}, reason=not_supported, "
                f"elapsed_ms={elapsed_ms:.2f}, error={exc}"
            )
            return Metric(
                source=source.name,
                symbol=symbol,
                ok=False,
                elapsed_ms=elapsed_ms,
                row_count=0,
                null_rate=1.0,
                skipped=True,
                error=f"not_supported: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            log(
                f"[ERR] source={source.name}, symbol={symbol}, attempt={attempt}/{MAX_ATTEMPTS}, "
                f"error={last_error}"
            )
            if attempt < MAX_ATTEMPTS:
                # Exponential backoff + jitter to reduce throttling risk.
                base = 0.7 * (2 ** (attempt - 1))
                jitter = random.uniform(0.2, 0.8)
                log(
                    f"[RETRY] source={source.name}, symbol={symbol}, sleep_s={(base + jitter):.2f}, "
                    f"next_attempt={attempt + 1}"
                )
                time.sleep(base + jitter)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    log(
        f"[FAIL] source={source.name}, symbol={symbol}, elapsed_ms={elapsed_ms:.2f}, "
        f"error={last_error or 'unknown error'}"
    )
    return Metric(
        source=source.name,
        symbol=symbol,
        ok=False,
        elapsed_ms=elapsed_ms,
        row_count=0,
        null_rate=1.0,
        error=last_error or "unknown error",
    )


def write_raw(metrics: List[Metric]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    with RAW_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(metrics[0]).keys()))
        writer.writeheader()
        for m in metrics:
            writer.writerow(asdict(m))


def write_summary(metrics: List[Metric]) -> None:
    rows = []
    grouped = {}
    for m in metrics:
        grouped.setdefault(m.source, []).append(m)
    for source, items in grouped.items():
        effective_items = [x for x in items if not x.skipped]
        success_rate = (
            sum(1 for x in effective_items if x.ok) / len(effective_items) if effective_items else 0.0
        )
        avg_ms = mean(x.elapsed_ms for x in items)
        avg_rows = mean(x.row_count for x in items)
        avg_null = mean(x.null_rate for x in items)
        rows.append(
            {
                "source": source,
                "success_rate": round(success_rate, 4),
                "effective_cases": len(effective_items),
                "skipped_cases": len(items) - len(effective_items),
                "avg_elapsed_ms": round(avg_ms, 2),
                "avg_row_count": round(avg_rows, 2),
                "avg_null_rate": round(avg_null, 4),
            }
        )
    pd.DataFrame(rows).to_csv(SUMMARY_CSV, index=False)


def write_report(metrics: List[Metric], precheck: Dict[str, str]) -> None:
    grouped = {}
    for m in metrics:
        grouped.setdefault(m.source, []).append(m)
    lines = [
        "# 数据源对比测试报告",
        "",
        "## 环境预检",
        f"- 代理环境变量: {precheck.get('proxy', 'unknown')}",
        f"- DNS(eastmoney主站): {precheck.get('dns_eastmoney_main', 'unknown')}",
        f"- TCP443(eastmoney主站): {precheck.get('tcp_eastmoney_main', 'unknown')}",
        f"- HTTPS(eastmoney主站): {precheck.get('https_eastmoney_main', 'unknown')}",
        f"- DNS(eastmoney港股): {precheck.get('dns_eastmoney_hk', 'unknown')}",
        f"- TCP443(eastmoney港股): {precheck.get('tcp_eastmoney_hk', 'unknown')}",
        f"- HTTPS(eastmoney港股): {precheck.get('https_eastmoney_hk', 'unknown')}",
        "",
        "## 测试范围",
        f"- 标的: {', '.join(SYMBOLS)}",
        "- 周期: 近 365 天日线",
        f"- 数据源: {', '.join(SELECTED_SOURCE_NAMES)}",
        "",
        "## 核心结果",
    ]
    for source, items in grouped.items():
        effective_items = [x for x in items if not x.skipped]
        success_rate = (
            sum(1 for x in effective_items if x.ok) / len(effective_items) if effective_items else 0.0
        )
        avg_ms = mean(x.elapsed_ms for x in items)
        lines.append(
            f"- {source}: 成功率={success_rate:.2%} (有效样本={len(effective_items)}, "
            f"not_supported={len(items) - len(effective_items)}), 平均耗时={avg_ms:.2f}ms"
        )
    lines.extend(["", "## 异常明细"])
    errors = [m for m in metrics if not m.ok and m.error]
    if not errors:
        lines.append("- 无")
    else:
        for e in errors:
            lines.append(f"- {e.source}/{e.symbol}: {e.error}")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    all_sources = {
        "akshare": AkShareSource(),
        "efinance": EFinanceSource(),
        "baostock": BaoStockSource(),
        "longport": LongPortSource(),
    }
    invalid = [name for name in SELECTED_SOURCE_NAMES if name not in all_sources]
    if invalid:
        raise ValueError(f"invalid source name(s): {invalid}, valid={list(all_sources.keys())}")
    sources = [all_sources[name] for name in SELECTED_SOURCE_NAMES]
    precheck = run_env_precheck()
    log(f"[CONFIG] selected_sources={SELECTED_SOURCE_NAMES}")
    log(f"[CONFIG] symbols={SYMBOLS}, date_range={start_date}~{end_date}")

    metrics: List[Metric] = []
    for src in sources:
        for symbol in SYMBOLS:
            metrics.append(run_single(src, symbol, start_date, end_date))
            cooldown = random.uniform(*THROTTLE_SECONDS)
            log(f"[THROTTLE] source={src.name}, symbol={symbol}, sleep_s={cooldown:.2f}")
            time.sleep(cooldown)

    write_raw(metrics)
    write_summary(metrics)
    write_report(metrics, precheck)
    log(f"[DONE] Reports saved in: {REPORT_DIR}")


if __name__ == "__main__":
    main()
