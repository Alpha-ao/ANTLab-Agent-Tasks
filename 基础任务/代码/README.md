# 代码入口

实际运行的代码保留在原目录。修改下面的源文件即可，不需要维护两套代码。

| 文件 | 用途 |
|---|---|
| [student_v2.py](../../基础/starter/student_v2.py) | 当前提示词与资料处理 |
| [student.py](../../基础/starter/student.py) | 首轮实验的冻结实现 |
| [serve_v2.py](../../scripts/serve_v2.py) | 本地页面后端 |
| [index.html](../../web/index.html) | 问答、引用与历史记录页面 |
| [score_exploration.py](../../scripts/score_exploration.py) | 从已有回答生成逐题结果 |
| [audit_improvement.py](../../scripts/audit_improvement.py) | 核对输入、结果与费用记录 |
| [test_basic.py](../../tests/test_basic.py)、[test_exploration.py](../../tests/test_exploration.py) | 基础任务测试 |

题目数据在[基础/data](../../基础/data/)。首轮配置在[configs/frozen.json](../../configs/frozen.json)，改进配置在[configs/evaluation_v2_thinking.json](../../configs/evaluation_v2_thinking.json)。
