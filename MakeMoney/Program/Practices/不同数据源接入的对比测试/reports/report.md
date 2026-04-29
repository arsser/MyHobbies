# 数据源对比测试报告

## 环境预检
- 代理环境变量: none
- DNS(eastmoney主站): ok
- TCP443(eastmoney主站): ok
- HTTPS(eastmoney主站): fail: HTTP Error 404: Not Found
- DNS(eastmoney港股): ok
- TCP443(eastmoney港股): ok
- HTTPS(eastmoney港股): fail: HTTP Error 404: Not Found

## 测试范围
- 标的: 600036, 00700.HK
- 周期: 近 365 天日线
- 数据源: baostock, longport

## 核心结果
- baostock: 成功率=100.00% (有效样本=1, not_supported=1), 平均耗时=224.05ms
- longport: 成功率=100.00% (有效样本=2, not_supported=0), 平均耗时=1764.28ms

## 异常明细
- baostock/00700.HK: not_supported: baostock does not support HK symbols in this benchmark