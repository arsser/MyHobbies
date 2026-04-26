uv 的目标是成为新一代的 Python 项目管理利器，它在 Mac 上的体验非常流畅。

安装：推荐使用 Homebrew，非常方便。


brew install uv
创建环境：在项目目录下，一条命令即可创建虚拟环境，无需指定 Python 版本，它会自动处理。


# 进入你的项目文件夹
cd my-project

# 创建虚拟环境（默认创建 .venv 文件夹）
uv venv

# 也可以指定 Python 版本，如果本地没有，uv 会自动下载
uv venv --python 3.12
激活环境：激活命令和标准的 venv 完全一样。


source .venv/bin/activate
管理依赖：uv 会自动生成 pyproject.toml 和 uv.lock 文件来锁定依赖版本，保证环境一致性。


# 添加依赖
uv add requests

# 移除依赖
uv remove requests
运行脚本：甚至不需要手动激活环境，uv run 会自动识别并使用环境。


uv run python script.py