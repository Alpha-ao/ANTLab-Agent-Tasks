# 代码入口

| 文件 | 用途 |
|---|---|
| [challenge.py](../../进阶/challenge_b/challenge.py) | 题包原样机，用于重现错误 |
| [fixed_engine.py](../../进阶/challenge_b/fixed_engine.py) | 修复缓存、范围筛选与引用状态 |
| [diagnostic_engine.py](../../进阶/challenge_b/diagnostic_engine.py) | 分别开关缓存与检索修复，比较原因 |
| [serve_b.py](../../scripts/serve_b.py) | 本地后端及请求记录 |
| [advanced_b.html](../../web/advanced_b.html) | 原版与修复版的对照页面 |
| [check_advanced_b.py](../../scripts/check_advanced_b.py) | 39 项行为检查 |
| [check_b_same_symptom.py](../../scripts/check_b_same_symptom.py) | 同一症状下的 12 项对照检查 |
| [audit_b.py](../../scripts/audit_b.py) | 核对实验、原版存档与诊断记录 |
| [test_b_http.py](../../tests/test_b_http.py)、[test_b_portability.py](../../tests/test_b_portability.py) | 输入错误处理和跨系统文件检查 |

以上都是实际运行文件。这里集中列出入口，不另复制一套源码。数据与正确行为要求在[challenge_b](../../进阶/challenge_b/)，未修改的原版存档在[versions/advanced_b](../../versions/advanced_b/)。
