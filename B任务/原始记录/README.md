# 原始记录

| 记录 | 内容 |
|---|---|
| [首轮行为检查](../../runs/advanced_b/verification/) | 故障复现、单独修复与回归检查 |
| [同症状对照](../../runs/advanced_b/same_symptom/) | 运行前预测、相同起始缓存和四组结果 |
| [模型诊断](../../runs/advanced_b/live_feedback/) | 3 类故障、3 种信息条件，共 9 次真实请求 |
| [最近行为复测](../../runs/advanced_b/recheck_20261009/) | 再次运行 39 项检查 |
| [最近同症状复测](../../runs/advanced_b/same_recheck_20261009/) | 再次运行 12 项对照检查 |
| [页面请求](../../runs/advanced_b/ui/) | 本地网页请求与程序返回 |
| [Linux 检查](../../results/advanced_b/linux-review.json) | WSL 实际运行命令与结果 |

模型只参与这 9 次诊断观察。代码修复后的行为由本地检查程序验证，两类记录分别保存。
