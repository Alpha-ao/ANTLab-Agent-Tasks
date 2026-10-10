# ANTLab Agent 考核项目

完成基础任务和进阶 B 题。按下面两个目录查看：

| 任务 | 内容 | 入口 |
|---|---|---|
| 基础任务 | 读资料、回答问题、给出引用，比较不同资料顺序下的结果 | [基础任务](基础任务/README.md) |
| B 任务 | 复现缓存、检索和引用状态错误，修改代码并检查结果 | [B任务](B任务/README.md) |

两个目录都包含简要报告、结果文件、代码入口和原始记录索引。先读各自的报告，再按记录查具体输入与输出。

## 本地运行

需要 Python 3.10 或以上版本，无需安装第三方库。在仓库根目录执行：

```powershell
python 基础任务/运行.py
# 或启动 B 题页面
python B任务/运行.py
```

基础页面：[localhost:8768](http://127.0.0.1:8768)。B 题页面：[localhost:8769](http://127.0.0.1:8769)。默认读取已保存的模型回答或执行本地程序，不产生 API 费用。已有服务运行时直接打开页面。

检查已有记录：

基础任务的 `--check` 用于原实验环境：它核对原始文件字节及未上传的本地配置，在全新下载目录中不能直接通过。下载后可运行 `python scripts/score_exploration.py` 离线复算答案结果；页面回放、单元测试和分类副本检查不需要该私有配置。

```powershell
python 基础任务/运行.py --check
python B任务/运行.py --check
python -m unittest discover -s tests -v
python scripts/organize_results.py --check
```

## 文件怎么放

- `基础任务/`、`B任务/`：分类后的阅读入口、报告和结果副本。
- `基础/`、`进阶/`：题包、数据和实际运行的代码。
- `scripts/`、`web/`、`tests/`：运行脚本、页面与测试。
- `runs/`、`configs/`、`versions/`：原始请求、实验配置和原版存档。
- `results/`：程序直接生成的结果及共用费用记录。

原始路径保留，两个分类目录需与整个仓库一起使用。更新实验结果后，运行 `python scripts/organize_results.py` 同步分类副本；每个目录的 `文件来源.json` 记录来源与文件校验值。

## 提交与核验

题包来源：[Shiina413/ANTLab-Agent-Tasks](https://github.com/Shiina413/ANTLab-Agent-Tasks)。修改前的源码基点为 `b028d90f43f44585cf085a3f607516a94f485e88`，保留上游及本地开发历史。

```powershell
# 查看提交版本；填写收集表时使用完整输出
git rev-parse HEAD
# 查看相对题包的改动
git diff b028d90f43f44585cf085a3f607516a94f485e88 HEAD
```

[整合报告](report.md) · [AI 使用声明](declaration.md) · [决定记录](decisions.md) · [考核规则](开始阅读.md) · [原仓库说明](原仓库说明.md)

本地实现和复测已完成。个人 Fork：[Alpha-ao/ANTLab-Agent-Tasks](https://github.com/Alpha-ao/ANTLab-Agent-Tasks)。基础任务的答案判分尚无独立人工复核；B 题的 9 次模型调用是诊断观察，不能当作自动修复成功率。用户本人仍需抽查关键结果，完成收集表提交。

分类副本的文本校验只统一 Windows/Linux 换行符，不忽略其他内容差异；图片按原始字节校验。历史实验的校验记录保持不变。

截至最近记录，共 195 次 API 请求，按所记录价格估算的费用上界约 1.094 元。历史详细记录仍在根目录的 `report-basic-v1.md`、`report-v2.md` 和整合报告中，分类报告中有对应入口。
