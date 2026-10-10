# 阅读与实现依据

访问日期：2026-10-08。只围绕本次基础任务；不把过去论文结果视为当前模型保证。

1. Lost in the Middle，TACL 2024（期刊，当前CCF/中科院评级尚未核实，不猜分区）。
   https://aclanthology.org/2024.tacl-1.9/ ，正文 https://arxiv.org/html/2307.03172v3 。
   §2.1/2.3通过改变相关文档位置观察问答表现，§4讨论架构、问题位置和指令训练，§5讨论增加检索文档的取舍。
   原实验主要是英文NaturalQuestions的单答案段场景，本任务是7段中文模拟记录，往往需要两段联合计算。
   因此这里只检验资料顺序，不能宣称复现U形曲线。K同时少了资料，不是纯位置对照。
2. ALCE，EMNLP 2023（会议；本记录未独立核实该年CCF分级）。
   https://aclanthology.org/2023.emnlp-main.398/ 。论文评价区分答案正确与引用支持，图2及引用评价部分说明
   应检查原文能否支持每条主张；§6是人工评价。我们沿用这一区分，不复现整套NLI模型指标。
   应用于本次：引用ID有效率与暂定答案正确率分别统计，不能用ID存在证明答案获支持。
3. DeepSeek官方当前接口与价格：
   https://api-docs.deepseek.com/zh-cn/quick_start/pricing/ ，https://api-docs.deepseek.com/guides/thinking_mode/ 。
   V4 Flash旧名实际映射V4.1 Flash；显式关闭默认思考模式以固定输出预算。
   高峰上界按输入2元/百万、输出8元/百万，缓存折扣不用于降低预算预留。

公开系统比较暂完成ALCE的评价设计阅读；第二个系统的深入比较留待整合报告，不冒充已完成。
本地端只测完整请求耗时，不推断GPU、服务端排队、prefill/decode或KV缓存机制。


## 第二个公开系统：Semantic Reader

来源：https://arxiv.org/abs/2303.14334 ，访问2026-10-08，阅读的是2023 v2预印本入口；本条不虚构会议评级。
作者报告用交互阅读界面帮助学者理解和浏览文档，涵盖阅读效率、理解、综合与可访问性。
与ALCE比较：ALCE关注生成答案及其引用支持的评价；Semantic Reader关注读者在原文中的阅读体验。
本次借鉴是把答案旁边直接展示本次引用原文并保留完整记录，便于核验；不将界面可定位宣称为语义正确。
没有亲测Semantic Reader用户研究或生产界面；该比较为作者资料分析，不是本项目的用户效果实验。

## 第二阶段模型配置

2026-10-08复核官方思考模式文档：enabled/disabled、low/high/max；思考模式不使用temperature。
https://api-docs.deepseek.com/guides/thinking_mode/ 。因此思考组显式low、4096输出上限，非思考组512。
实际成本按API usage计入同一10元上限，参数差异公开，不能据此声称等计算预算提升。
