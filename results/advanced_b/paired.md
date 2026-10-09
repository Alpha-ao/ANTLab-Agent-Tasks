# B题逐例结果

来源：runs/advanced_b/verification/paired.json；复算：python scripts/summarize_b.py。

| 案例 | 原版证据 / 状态 | 修复版证据 / 状态 | 原版请求ID | 修复版请求ID |
|---|---|---|---|---|
| R01 | b01 / supported | b01 / ok / not_checked | b6a0da2b-b847-46f4-ba4e-4dc65a76d493 | b861ba6b-c486-464d-8ba1-56c03e3a9843 |
| R02 | b01 / supported | b02 / ok / not_checked | 66cd7e9d-463d-4a7a-86a8-5c7f0755eddd | e22d42e5-720d-40eb-9ad5-0635fcba2cef |
| R03 |  / not_checked | b03 / ok / not_checked | 3f02e3ea-b6e9-4a96-8841-a49c91b24b0a | 1abf7f01-d639-408d-abfc-374b290eda7b |
| R04 | b04 / supported | b04 / ok / not_checked | d577846c-68a3-4038-aefa-6ab91809cdcc | 4c0eb90c-0628-4b5e-9bc6-afdc75c8bf6c |
| R05 | b05 / supported | b05 / ok / not_checked | 288f4c93-66a7-42c6-a47b-5e214e831baa | 45d765ea-1fb8-40ce-819c-e5d0ec8a5eba |
| R06 | b06 / supported | b06 / ok / not_checked | 78c7b220-a502-47d8-bc95-4bc5b03c8c4a | 67a11c08-67ba-46fb-927c-9250380d951a |
| R07 |  / not_checked |  / invalid_scope / not_checked | 6de92031-791e-4749-9f14-febbc2ddf3ee | 337b3b52-46c8-4df9-945f-1daf2354deda |

语义状态全部未核验不等于答案全部正确。修复保持固定draft不变。

## DeepSeek外部信息诊断（AI定性复核）

- version / category / 0d46089f-96aa-478a-a57f-93054709dccb：区分版本问题并列出多个原因，未获得具体日志，不能确认原因。
- retrieval / category / 1537ea7e-705d-4663-a12e-ffa83825d1fa：提出候选阶段日志与较大k对照，但仍有多个假设。
- version / evidence / 320fe13b-292e-40a3-bd9b-6d878bca5088：结合v2请求、b01和cache_hit提出清缓存对照；E1实际为输入草稿，不能称其为独立执行结果。
- support / category / 3ed72f7d-4392-4fdf-8513-5b4bed342e37：明确区分定位与语义，建议分开检查。
- retrieval / evidence / 76b7443f-30e6-4bb4-8d04-66424eb14a02：结合b01/b02与中间选择轨迹，给出k=2检查与筛选顺序修复方向。
- support / symptom / 8576b09c-baec-49bd-9312-1364cc7d56ae：建议逐句核对证据；无法凭现象确定引用和语义是否混淆。
- retrieval / symptom / 89dd07a2-0b5c-47f5-9178-9a2548c5665a：已提出先截取再过滤的候选解释；因此有证据组不能被说成首次发现原因。
- version / symptom / ba66aeef-06ee-4681-8767-30a713875078：把答案中的30秒误读为响应耗时；原始现象表述有歧义，不能只归因模型。
- support / evidence / bfce4c3d-8964-49f3-82d9-32f4abfbd2f8：指出原文未测量GPU释放，不能支持保证释放；未测量也不能证明现实中绝不释放。
