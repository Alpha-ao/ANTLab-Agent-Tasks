# B任务：故障诊断与修复

检查文档查证程序为什么返回旧版本、漏掉证据或错误显示“已验证”，保存故障和修复前后的结果。

| 内容 | 文件 |
|---|---|
| 项目说明与结果 | [报告.md](报告.md) |
| 详细记录 | [报告目录](报告/) |
| 代码入口 | [代码目录](代码/) |
| 原始记录索引 | [原始记录目录](原始记录/) |
| 逐例结果、模型诊断、复测和截图 | [结果目录](结果/) |
| 阅读资料与实验设计 | [资料与方案.md](资料与方案.md) |
| 原题 | [B任务原文](../进阶/02_B_系统失效诊断.md) |
| 正确行为要求 | [spec.md](../进阶/challenge_b/spec.md) |
| 原版与修复代码 | [原版](../进阶/challenge_b/challenge.py)、[修复版](../进阶/challenge_b/fixed_engine.py) |
| 页面与后端 | [页面](../web/advanced_b.html)、[后端](../scripts/serve_b.py) |
| 原始实验记录 | [runs/advanced_b](../runs/advanced_b/) |
| 同症状对照预测 | [配置](../configs/advanced_b_same_symptom_plan.json) |
| 原样机存档 | [versions/advanced_b](../versions/advanced_b/) |

在项目根目录运行：

```powershell
python B任务/运行.py
```

打开 http://127.0.0.1:8769 。分别选择原样机和修复版，点击“版本切换演示”。
页面只执行本地程序，不收费；下方模型诊断读取已经保存的结果。已有服务运行时不必再次启动。

检查记录，或新建一轮离线实验：

```powershell
python B任务/运行.py --check
python scripts/check_advanced_b.py --label review_new
python scripts/check_b_same_symptom.py --label same_review_new
```

每轮目录名必须未使用，防止覆盖旧记录。分类结果副本的来源见[文件来源.json](文件来源.json)。
本目录和基础任务共用根目录的代码与记录，需保留整个仓库。
