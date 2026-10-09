# 基础任务与进阶B整合报告

2026-10-09。作者工作由Codex辅助；用户本人核验尚未完成。上游基点：b028d90f43f44585cf085a3f607516a94f485e88。

## 1. 完成概览

选择基础任务＋B系统故障诊断。本地开发与实验已完成，GitHub个人仓库与收集表尚未提交。
基础保留冻结的40次主请求，后续改进另列探索。进阶保留原样机7条结果、四条件干预、39项离线检查、9次DeepSeek真实诊断和浏览器操作日志。
最值得检查的三个结果：

- runs/advanced_b/baseline.json中的R02：请求v2，却返回v1的30秒与b01。
- runs/advanced_b/verification/interventions.json：只修缓存仍漏证据，只修检索仍复用旧答案。
- runs/advanced_b/ui/5eaf794f-2f6c-4288-ba71-3c3cc2603d16.json：修复网页经过后端，返回v2的12秒与b02；results/advanced_b/ui-result.png为浏览器截图。

尚未实现：通用语义验证器、自动改代码的Agent、多worker/多用户服务。不能把not_checked当作“答案已正确”。

## 2. 阅读到命题

ALCE（EMNLP 2023）的第3.3节将引用支持与无关引用分别评价；第5节比较不同生成方法，第6节人工评价。实验使用ASQA、QAMPARI、ELI5，主模型为ChatGPT，同时测试GPT-4及开源模型。我们的迁移命题是：引用能定位并不保证回答得到支持。B的R04正好可以反驳“ID合法就supported”。我们没有移植它的NLI裁判，也没有复现其效果数字。
论文：https://aclanthology.org/2023.emnlp-main.398/ 。CCF官网2017条目列EMNLP为B类，未核实2026新版目录。

P1规则1/5/9要求保留来源、中间结果和结论依据，因此保留原程序、输入、输出与请求顺序。
P2规则6/7强调版本管理与可重复流程，因此新增脚本和固定输入，不靠手工改JSON制造修复。
两篇发表于PLOS Computational Biology，本次未核实中科院分区；它们是实践建议，不是本任务效果的实验依据。
P1：https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285
P2：https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007007

RFC 9111第2/4.1节说明缓存复用依赖请求条件。本项目借用其原则，将请求、资料内容、draft与实现版本纳入缓存身份，不声称实现HTTP缓存协议。
https://www.rfc-editor.org/rfc/rfc9111.html

项目比较：Haystack元数据过滤适合借鉴文档/版本范围限制，但题包用固定tags，换成向量检索会改变题意；LlamaIndex CitationQueryEngine适合借鉴可读引用片段，但生成引用不是语义核验。这两项是官方文档分析，没有安装并亲测框架。
https://docs.haystack.deepset.ai/docs/metadata-filtering
https://developers.llamaindex.ai/python/examples/query_engine/citation_query_engine/

## 3. 实验设计

**二次审查补正**：下述首轮四条件覆盖两个不同症状，不能单独满足“同一症状的两个原因”要求。
为此另建configs/advanced_b_same_symptom_plan.json，在对应运行前保存预测，执行记录见runs/advanced_b/same_symptom。
统一症状为alpha/v2、k=1返回空证据。用未修改原样机运行R03，自然生成一个空结果缓存；四组都从它的同一副本开始，目标请求、资料和draft完全相同。
H1认为空缓存被错误复用；H2认为即使重新计算，全库先截取k=1也会丢失b02。两者都与源码和初始症状相容，但作用边界不同。
预测：仅改范围仍命中空缓存；仅改缓存会重新算出空证据；两处都改恢复b02。冷启动对照和k=2负对照用于分离两机制。
这是看到源码和先前结果后的追加实验，不称盲发现，也不改写首轮记录。

研究对象是合成离线Engine，固定draft有意包含错误。所有输入公开、已读源码，不称盲测。
事前预测在configs/advanced_b_plan.json和work/deep-interview/advanced-b.md；实际运行哈希在runs/advanced_b/verification/manifest.json。

主问题：相同query在版本切换后错误复用答案。源码已确认query-only缓存，因此不虚构“模型幻觉”竞争解释。仍待区分的是：仅修缓存是否足以保证证据来自当前范围且不漏选？
H1缓存解释：原k=2的v2请求清空缓存后应恢复b02；H2检索解释：即使冷缓存，先全库截取k=1再过滤仍会漏掉b02。两者可以共同存在，但后者不能解释所有旧答案。

四条件只改变缓存/筛选顺序两个因素：原版、只改缓存、只改范围、两者都改。每组执行相同v1→v2序列，再独立执行冷缓存v2/k=1边界，draft不变。观察旧答案是否出现、b02是否丢失，而非只看返回200。源码插桩另在7条原案例核对，与原实现输出一致。

DeepSeek扩展为3类故障×3种信息条件：仅现象、现象＋作者提供类别、再加实际日志/原文。配置与所有messages在configs/advanced_b_feedback.json冻结后运行。模型deepseek-flash，low思考，max_tokens=4096，每条件一次，无重试。类别由实验作者提供，不是模型自己发现；输入长度不同，仅输出上限相同。
这项实验测诊断内容，不测自动修复。没有隐藏测试反馈给模型，也没有把正确补丁发给它。API错误、截断、JSON/usage异常或超预算停止，错误诊断保留为结果。本轮9次无技术失败。

## 4. 实现与复现

页面 → /api/run → 请求与范围检查 → 缓存查找 → 范围内排序/截取 → 引用合法性检查 → 返回原文和状态 → 同request_id日志。
页面为web/advanced_b.html，后端scripts/serve_b.py，修复进阶/challenge_b/fixed_engine.py。

修复采用保守精确缓存：请求字段、排序后的语料内容、固定draft、实现版本共同摘要。允许重复请求命中；参数/内容改变必须重新算。返回深拷贝，避免调用方修改缓存；每次生成新请求ID，保留首次来源ID。
只保留正分候选，同分按ID排序，先选范围再取k。未知范围和重复证据ID明确拒绝。无引用与越界引用分别标absent/invalid。引用规则来源为rule，语义判断来源为unverified，support_status=not_checked。

原样机完整保存在versions/advanced_b；题包challenge.py、data.json没有修改。原baseline结果不覆盖。新增代码由Codex编写，DeepSeek只参与9次诊断，没有自动修改代码。

启动：python scripts/serve_b.py --port 8769。默认只有本地离线重放，不收费。
复核：python scripts/check_advanced_b.py --label review_01（目录名需未使用）；python scripts/summarize_b.py；python scripts/audit_b.py。
基础复核：python -m unittest discover -s tests -v；python scripts/audit_improvement.py。
付费脚本为scripts/run_b_feedback.py，已有记录时拒绝重跑。密钥只在本机环境变量，配置不提交。预算账本不支持跨进程并行写入。

## 5. 结果与诊断

### 基础历史

首轮40主请求：R0 4/8、R1 4/8、R2 3/8、K 1/8、排序改进3/8，排序没有展示净收益。
后续新提示＋low思考在完整资料四条件均8/8，属于已见题探索，且增加推理预算，不能归因排序。16条明确压力检查通过，M01因剩余计数可推分母而存在题目歧义，原记录保留。候选标签没有独立人工金标准。
详见report-basic-v1.md、report-v2.md、results/results.csv与results/exploration.csv。

### B核心结果

下表来源runs/advanced_b/verification/interventions.json，逐次请求ID与完整输入见同目录raw.json。重跑check_advanced_b.py可复算。

| 条件 | 热缓存v2仍用旧答案 | 冷缓存v2/k=1漏b02 |
|---|---|---|
| 原版 | 是 | 是 |
| 只改缓存 | 否 | 是 |
| 只改范围 | 是 | 否 |
| 两者都改 | 否 | 否 |

最早错误边界：版本切换在cache lookup复用旧包时发生；漏检在全库top-k截取时发生；虚假supported在引用合法性替代语义检查时发生。前两个可独立触发，符合事前预测。

原7条配对：R02修复版本；R03恢复b03；R04仍保留原错误draft，但不再假称已核验；R05/R06正常答案和引用保留；R07拒绝未知文档。全部逐例结果与run ID见results/advanced_b/paired.md。
39项离线检查全部通过，包括2个正常回归、语料逆序/ID重映射、资料与参数变化、返回对象修改、未知版本、部分文档缺版本、多文档查询、无引用、越界引用、无匹配、重复ID和非法k。
这些是断言数量，不是39个独立故障。有限合成测试不证明生产可靠性。

反向检查：精确缓存逐步与无缓存执行比较，答案/证据/状态一致；重复请求ID不同且来源ID可追溯。离线时间不代表LLM速度；没有用更快作为修复成功依据。全not_checked只消除虚假验证，不能当作语义正确率提高。
浏览器实测原版v1→v2仍30秒、修复版30→12秒；手工输入v999得到invalid_scope。各次原始日志在runs/advanced_b/ui。

### 同一症状的追加结果

下表来源runs/advanced_b/same_symptom/summary.json；输入、初始缓存和每次request_id见raw.json。复跑命令：python scripts/check_b_same_symptom.py --label independent_review（目录需不存在）。

| 条件（同一v2/k=1请求） | 是否复用旧缓存 | 证据 |
|---|---|---|
| 原版 | 是 | 空 |
| 只修缓存 | 否 | 空 |
| 只修检索 | 是 | 空 |
| 两处都修 | 否 | b02 |

冷启动原版仍为空，冷启动且修检索得到b02，证明重新计算也可能失败。
改用k=2且保留同一初始缓存时，原版为空，仅修缓存即恢复b02，表明缓存机制有可独立观察的作用。
因此，暖缓存请求的最早错误在复用边界；消除此错误后，检索顺序仍可使同一症状持续。新增12项检查通过。

页面补测5项通过：{}请求、非法JSON、正常版本演示、演示后单次执行、模式切换。见results/advanced_b/ui-review-checks.json及ui-error-fixed.png。
接口对JSON数组/null/数字/字符串返回400，原版模式缺字段也明确拒绝。服务已重启加载修正。
跨系统路径读取修复后，在Ubuntu WSL、Python 3.12.3对同一工作目录实际复跑39项与12项检查及单元测试；并非一台全新Linux服务器或全新GitHub克隆的验证。见results/advanced_b/linux-review.json。

### 外部信息诊断（辅助观察，不作为有效性证明）

逐例输出及Codex定性复核在results/advanced_b/summary.json、paired.md；复算python scripts/summarize_b.py。不用关键词打出虚假的诊断准确率。
有具体证据时，模型将b01/b02和cache_hit用于版本诊断，将中间候选轨迹用于漏检诊断，将未测量GPU释放的原文用于反驳强断言。
但检索案例仅凭现象就已提出正确的候选原因，所以不能说“只有外部信息才能发现”。版本案例“返回30秒”表述含糊，无信息组误读为耗时，新增信息同时消除了歧义；该例不能干净证明反馈类型的独立作用。保留原始失败，没有改题重跑。
有证据组也并非完美：版本回答将E1输入草稿说成返回；支持回答中“未测量”只能说明缺依据，不能推出客观上绝不释放GPU。模型建议的“部分支持”也不直接写入题包枚举。

9次诊断费用高峰估算上界0.070746元，累计195次请求1.093666元，非实际账单。三组客户端耗时中位数分别约7.755/5.311/7.883秒；每组仅3条且输入长度不同，不宣称速度优势。全部原始usage保留。

## 6. 决定与未来

保留范围内检索、精确缓存、清楚区分引用与语义状态；停止在这3个已知故障上继续调提示或追求全对。三个关键决定及替代方案见decisions.md。
没有采用仅补snapshot字段：它仍无法隔离k、文档、资料内容与draft变化。没有只关缓存作为最终方案：无缓存作为正确性参照，精确缓存保留合法复用。没有用模型supported输出充当裁判：模型诊断也存在上述失误。

接入真实系统时需要明确资料不可变版本、提示/模型配置版本、trace_id、实际证据ID、缓存来源ID、取消状态。长期约束主要是版本维护与评价依据维护，不能只更新模型而沿用旧结论。
应用—推理联合实验：固定输入/输出长度和并发，分别记录应用缓存命中、排队、prefill、decode、取消确认和资源释放时间。假设“页面取消代表服务端停止计算”会被取消后继续产生服务端计算记录推翻。本次没有这些服务端字段，不能下GPU结论。
多worker后本地缓存不共享且更新时机不同。下一步双worker交替读写版本，以是否返回错误版本作为失败标准；一旦出现就停止性能优越性结论。与模型KV Cache无关，不能混称。

证据索引：E1网页与ui日志；E2本报告第2节与work/deep-interview/advanced-b.md；E3 baseline、verification/paired、live_feedback；E4事前plan与interventions；E5 checks与variants；E6 decisions.md；E7 configs、declaration.md。用户本人复核与GitHub提交仍需完成。
