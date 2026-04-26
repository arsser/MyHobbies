# MakeMoney 项目说明

这是一个围绕交易策略、量化研究与回测分析的个人实践仓库，目标是把策略想法、研究过程和落地代码沉淀为可复用资产。


## 环境准备

采用“父目录统一环境”方式：在 `MakeMoney/` 的父目录创建一个共享虚拟环境，`MakeMoney` 直接复用。

```bash

cd MakeMoney/Code
# 假设当前在仓库根目录（MakeMoney 的父目录）
uv venv .env

# 进入 MakeMoney 开发前激活父目录环境
source ./quant-env/bin/activate
```

安装包：
uv add yfinance pandas matplotlib

