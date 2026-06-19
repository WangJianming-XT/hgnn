# rivermind-data

这是仓库 `rivermind-data` 的代码树，包含 GFM-RAG 相关的数据处理、基准测试和实验脚本。

主要目录与说明：

- `gfm-rag-main/`、`gfm-hybrid-hypergraph/`：主要实现和数据目录。
- `hypergraph-rag-prototype/`：原型与实验脚本。
- `models/`：训练或下载的模型文件（通常应在 `.gitignore` 中忽略）。
- `cache/`、`outputs/`、`tmp/`、`venvs/`：运行时产生的缓存与虚拟环境，应忽略。

快速开始：

1. 建议创建并激活 Python 虚拟环境：

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. 查看项目脚本并按需运行，例如：

```bash
python run_five_real_samples.py
```

注意：仓库包含较大的数据文件与模型，请在上传到 GitHub 前确认是否需要将大文件迁移到 Git LFS 或另行存储。

---

如果你希望我把当前目录结构同步到 GitHub 仓库 `WangJianming-XT/hgnn`，请确认是否允许我将本地提交推送到该远程（是否允许覆盖远端同名分支）。
