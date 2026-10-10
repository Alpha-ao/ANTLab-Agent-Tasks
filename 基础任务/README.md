# 基础任务

根据给定资料回答问题，给出引用，并比较不同资料顺序和选择方式对回答的影响。

| 内容 | 文件 |
|---|---|
| 项目说明与结果 | [报告.md](报告.md) |
| 首轮、改进过程 | [报告目录](报告/) |
| 逐题表、检查记录、截图 | [结果目录](结果/) |
| 阅读资料 | [阅读记录](资料/阅读记录.md) |
| 代码入口 | [代码目录](代码/) |
| 原始记录索引 | [原始记录目录](原始记录/) |
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

```powershell
python 基础任务/运行.py --check
```

本目录的结果文件是原始结果的分类副本，来源和校验值见[文件来源.json](文件来源.json)。
原始请求与冻结代码没有移动。若重新生成了结果，在根目录执行 `python scripts/organize_results.py` 更新分类副本。
