# 基础任务

根据给定资料回答问题，给出引用，并比较不同资料顺序和选择方式对回答的影响。

| 内容 | 文件 |
|---|---|
| 项目说明与结果 | [报告.md](报告.md) |
| 首轮、改进过程 | [首轮报告](../report-basic-v1.md)、[改进报告](../report-v2.md) |
| 逐题表、检查记录、截图 | [首轮逐题表](../results/results.csv)、[改进逐题表](../results/exploration.csv)、[检查记录](../results/completion_audit.json)、[截图](../results/ui-verified.jpg) |
| 阅读资料 | [阅读记录](../research.md) |
| 原题 | [基础任务说明](../基础/01_考核题目.md) |
| 题目数据、原始代码 | [基础目录](../基础/) |
| 当前提示词实现 | [student_v2.py](../基础/starter/student_v2.py) |
| 页面与后端 | [页面](../web/index.html)、[后端](../scripts/serve_v2.py) |
| 首轮实际请求 | [runs/basic](../runs/basic/) |
| 后续实验请求 | [runs/exploration](../runs/exploration/) |
| 配置 | [首轮冻结配置](../configs/frozen.json)、[改进配置](../configs/evaluation_v2_thinking.json) |

在项目根目录运行：

```powershell
python 基础任务/运行.py
```

打开 http://127.0.0.1:8768 。默认提供预览和历史记录，不调用付费API。
已有服务正在运行时直接打开页面即可。

检查已保存的结果：

以下检查依赖原实验环境的本地配置和原始文件字节；下载仓库后，使用 `python scripts/score_exploration.py` 离线复算答案结果。不要为通过原环境检查上传私有配置。

```powershell
python 基础任务/运行.py --check
```

报告和结果直接链接到原文件，不另存副本。运行时需保留整个仓库。
