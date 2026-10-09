# ANTLab：基础任务与进阶B

## 当前交付（2026-10-09）

二次审查后的修正：新增针对同一“v2证据为空”症状的四条件对照，12项检查通过；原39项保留。
网页已修复空请求/错误JSON渲染、旧结果和旧演示顺序残留，并直接显示核验来源。
Ubuntu WSL / Python 3.12.3已实际复跑39项＋12项和单元测试；记录见results/advanced_b/linux-review.json。
原9次模型诊断仅作为辅助观察，不计算反馈提升率；本轮没有新增API费用。

B题已完成本地诊断、修复与浏览器验证；基础历史结果保留。
主问题是版本切换误用旧缓存，另修正范围外条目挤占检索名额和虚假supported状态。
39项离线检查通过；DeepSeek V4.1 Flash新增9次真实诊断请求，无自动重试。
这9次研究外部信息怎样帮助诊断，没有让模型自动修改代码，也不代表自动修复成功率。
版本现象的描述有歧义，保留失败，不据此声称外部反馈普遍有效。
累计195次API请求，高峰价格估算上界1.093666元，仍在10元上限内。

[整合报告](report.md) · [B逐例结果](results/advanced_b/paired.md) · [B计划与资料](work/deep-interview/advanced-b.md)

```powershell
python scripts/serve_b.py --port 8769
# 另一个终端运行；离线，不收费。label不得复用已有目录。
python scripts/check_advanced_b.py --label my_review_01
python scripts/check_b_same_symptom.py --label my_same_symptom_01
python scripts/summarize_b.py
python scripts/audit_b.py
```

打开 http://127.0.0.1:8769 ，分别在原样机/修复版点击“版本切换演示”。
可编辑请求、查看实际版本、引用原文及对应请求日志；下方显示9条已保存的真实模型诊断。
页面重放只执行本地程序，不发API请求。原始模型响应含在runs/advanced_b/live_feedback。
`scripts/run_b_feedback.py --run`是付费命令，需要本地配置与ASSESSMENT_API_KEY，且已有首轮记录时拒绝重跑。
部署范围仅本机单进程，不提供多用户生产服务；不要并行启动多个付费执行器。
Python 3.10+，标准库即可。本机实测Python 3.14。

题包原样机在versions/advanced_b，新增fixed_engine.py为修复实现，diagnostic_engine.py只用于四条件干预。
上游基点b028d90f43f44585cf085a3f607516a94f485e88；本人工作由Codex辅助，尚需用户亲自核验。
查看全部改动：`git diff b028d90f43f44585cf085a3f607516a94f485e88 HEAD`；最终本地版本：`git rev-parse HEAD`。
尚未完成个人GitHub Fork/推送、收集表与独立人工复核；这些不以本地运行代替。

历史manifest保持不变。跨系统读取同时支持Windows和POSIX相对路径；补充manifest只允许CRLF/LF换行等价，不忽略代码或数据内容变化。

## 基础推荐版本（2026-10-08历史记录）

使用 **v2提示词 + low思考模式 + 完整资料原序**。已见8道评测题在R0/R1/R2/排序四组均8/8暂定正确；
新长文本/缺资料检查16/16通过，另保留1条测试本身有歧义的记录。不是独立人工盲评。
K检索仍有失败，不作为推荐默认路径。累计186次真实请求，费用高峰估算上界约1.023元。

[当前报告](report-v2.md) · [探索逐题表](results/exploration.csv) · [界面验收](results/ui-verified.jpg)

```powershell
python scripts/serve_v2.py --port 8768
python scripts/score_exploration.py
python -m unittest discover -s tests -v
```

打开 http://127.0.0.1:8768 。默认仅预览与回放。网页真实API、原文引用、日志对应及额度拒绝已实测。
付费模式须显式设置 `--paid-limit 1` 并提供环境变量ASSESSMENT_API_KEY；全部计入10元账本。
付费执行器串行运行，尚不支持多个进程同时改写预算账本。
首轮冻结的student.py不改写；推荐实现位于student_v2.py，历史与探索分别保存。

以下为首轮历史说明（后续状态以本节和report-v2.md为准）。

本地目录：E:/project/AI_Agent/ANTLab-Agent-Tasks。已克隆上游，尚未创建自己的GitHub Fork或推送。
上游源码基点：b028d90f43f44585cf085a3f607516a94f485e88。
查看修改：`git diff b028d90f43f44585cf085a3f607516a94f485e88`（新文件另见git status）。

- [首轮报告](report-basic-v1.md)、[执行决策](decisions.md)、[AI声明](declaration.md)
- [逐题结果](results/results.csv)、[配对结果](results/paired.json)、[费用上界](results/budget.json)
- [诊断](results/diagnostic.json)、[变体检查](results/variants.json)、[冻结配置](configs/frozen.json)

Python 3.10+，仅标准库；本机实测Python 3.14.3。

```powershell
python -m unittest discover -s tests -v
python scripts/analyze_basic.py
python 基础/starter/server.py --config 基础/config.local.json
```

打开 http://127.0.0.1:8765 。页面可回放已有结果；默认不启用付费调用。
本地配置不入Git。新环境复制基础/config.example.json为基础/config.local.json，填写所用公开接口与模型；
参数可参考configs/frozen.json的config字段，密钥只通过ASSESSMENT_API_KEY环境变量传入。

`python scripts/run_basic.py dev`与`evaluation`会产生费用，已有轮次拒绝重复执行。
不要为继续运行而删除旧结果；追加实验应单独命名并保留原始冻结轮次。
已有结果复算不需要密钥、不调用模型。当前冻结哈希包括本地配置文件字节，换环境需还原配置才能通过。

已完成：核心输入与排序逻辑、8次开发+40次正式API请求、5项单元测试、12题离线变体、逐例候选核查。
待完成：独立人工核验；浏览器按钮真实请求验证；第二公开系统比较；进阶题；个人Fork与提交。
页面真实生成验证遭遇浏览器交互阻塞，没有产生额外API记录，不能算前后端完整闭环已验证。
模型质量有退步：R0暂定4/8，改进3/8；引用ID有效不等于内容支持。详见报告。

---

# ANTLab Agent Tasks

文档阅读与信息核验方向 Agent 项目的应用层开发者招募考核：先完成基础题，再从进阶 A/B/C 中选择一套完成。

**截止时间：北京时间 2026 年 10 月 16 日 23:59（UTC+8）。**

## 从哪开始

1. 先读 [开始阅读.md](开始阅读.md)（总体规则、时间、提交方式）。
2. 基础题（必做）：[基础/README.md](基础/README.md) 与 基础/01_考核题目.md。
3. 进阶题（三选一）：[进阶/README.md](进阶/README.md)，在 A / B / C 中选一套。

## 目录结构

```text
开始阅读.md              入口：总体规则、截止时间、提交方式
基础/                    基础题：12 题（4 开发题有公开答案 + 8 评测题），
                         R0/R1/R2/K 四种输入组织条件；模型 API 自费，
                         主请求量与运行命令见 基础/README.md
进阶/                    进阶题（A/B/C 三选一）
├─ 01_A_研究机制迁移.md        A：主张→证据→支持状态机制迁移与对照
├─ 02_B_系统失效诊断.md        B：源码审查、故障归因与修复
├─ 03_C_产品假设验证.md        C：围绕自选用户任务的产品假设验证
├─ materials/                 两份 CC Attribution 公开论文（P1/P2）及抽取数据
├─ challenge_b/               B 题文档查证样机（30 行 Engine，含预埋故障）
└─ templates/                 声明与整合报告模板
```

## 规则要点

- 准备时间为一周（包含基础题和进阶题）；模型调用使用自己的 API，费用自理；实验输入、原始响应、失败和前后对照须保留在仓库中。
- AI 可辅助阅读、实现和排错；需记录它对关键决定的影响、本人如何核验，以及实际完成和未完成的内容。
- 提交：把作品推送到自己的 GitHub 仓库，并在收集表登记仓库链接与最终 commit SHA；收集表地址与仓库评审账号见 Q 群公布（详见 进阶/05_提交与报告格式.md 与 进阶/06_收集表填写说明.md）。
- 本包不含评委参考答案、评测标签、内部开发教程或商业书籍全文。
- 文件完整性：`基础/文件校验.json` 与 `进阶/文件校验.json` 提供逐文件 SHA256，可自行校验。
