# FINAL MAP：可以突出哪些 findings？

更新：2026-10-07。依据当前 `data/lit-map 2026s sycophancy - FINAL MAP.csv` 的 31 篇文献及原有人工编码。统计单位是“文献/CSV 行”，不是参与者、实验或相互独立的实证研究。

建议主线：**不同 sycophancy 定义对应的结果指标覆盖不均衡；系统表现与用户结果很少在同一篇文献中共同出现，尤其缺少用户任务表现的编码。** 这是当前纳入文献的描述性发现与后续研究方向，不是对整个领域的完整普查结论。

## 优先 finding 1：系统与用户结果很少共同覆盖

英文标题：**Limited co-coverage of system performance and user outcomes in the mapped corpus.**

把 User opinion、User action、User performance 中至少一项被标记，定义为“用户结果”。对原始 CSV 按 DOI 去重后：

| 互斥分类 | 文献数 | 占全部 31 篇 |
| --- | ---: | ---: |
| 仅用户结果 | 14 | 45.2% |
| 仅系统表现 | 11 | 35.5% |
| 同时标记两者 | 1 | 3.2% |
| 两者均未标记，对应 Outcomes / None | 5 | 16.1% |

用户结果合计 15 篇，系统表现合计 12 篇；它们的交集只有 1 篇。26 篇至少标记一种结果的文献中，联合覆盖占 1/26（3.8%）。

唯一同时被编码为系统与用户结果的文献是 **When AI Gives Advice: Evaluating AI and Human Responses to Online Advice-Seeking for Well-Being**（DOI `10.1145/3772318.3791233`），当前勾选的是 User opinion 和 System performance。

意义：可以提出未来研究同时记录模型/系统表现与人的感受、行为及任务表现。但共同标记不等于该论文已经直接检验两者关系；没有共同标记也不能证明论文全文从未讨论两者。

这是回到逐篇 CSV 计算的新统计。现有三张热图没有“结果 × 结果”这张表，**不能直接把热图的格子相加来得到这个交集**。

可直接使用的英文：

> Under the current coding, 15 of the 31 mapped publications included at least one user-related outcome and 12 included system performance, but only one was coded for both [20]. This limited co-coverage motivates evaluations that connect system-level performance with user perceptions, behavior, and task performance.

## 优先 finding 2：用户任务表现是较少覆盖的结果指标

英文标题：**User task performance is less frequently coded than perceptions, behavior, or system performance.**

| Outcomes 属性 | 文献数 | 占全部 31 篇 |
| --- | ---: | ---: |
| System performance | 12 | 38.7% |
| User opinion | 11 | 35.5% |
| User action | 8 | 25.8% |
| User performance | 4 | 12.9% |
| None（只直接测量 sycophancy、不编码其他影响） | 5 | 16.1% |

这些属性不是互斥分类，不能直接相加。User performance 在 15 篇有用户结果的文献中占 4/15（26.7%）。

可以强调：当前文献地图较少覆盖用户能否把任务做得更好或更差，这为增加任务层面的测量提供理由。不能据此说 sycophancy 对用户表现的影响较小，也不能说“用户研究很少”：15/31 篇已有至少一种用户结果标记。

四篇 User performance 的 DOI：`10.1145/3717511.3747073`、`10.1145/3742413.3789120`、`10.1145/3772318.3790934`、`10.1145/3772318.3791365`。完整标题见文献库和审计表。

可直接使用的英文：

> User performance was coded in only four publications (12.9%), compared with user opinion in 11, user action in eight, and system performance in 12. The mapped corpus therefore provides comparatively limited coverage of the sychopancy's effect on users' task performance, motivating its inclusion alongside perception and behavior measures.

## 优先 finding 3：不同定义对应不同的结果指标覆盖

英文标题：**Outcome coverage varies across operationalizations of sycophancy.**

下表分母是该定义的文献数，不是全部 31 篇；“用户结果”仍是三种用户指标的去重并集。

| 定义标签 | 文献数 | 同时标记系统表现 | 同时标记至少一种用户结果 |
| --- | ---: | ---: | ---: |
| Hallucination Agreement | 4 | 4/4（100%） | 0/4 |
| Bias Agreement | 13 | 4/13（30.8%） | 7/13（53.8%） |
| Obsequiousness | 7 | 0/7 | 4/7（57.1%） |
| Stance Change | 8 | 5/8（62.5%） | 3/8（37.5%） |
| Failure to challenge/trying to get along | 17 | 6/17（35.3%） | 8/17（47.1%） |

最清楚的两个观察是：Hallucination Agreement 的四篇都标记 System performance，而没有用户结果；Obsequiousness 的七篇没有标记 System performance，其中四篇有用户结果，其余三篇标记 None。

可把这些视为值得进一步核对的“定义—测量覆盖差异”，以及当前样本中的候选研究空白。不能写成“幻觉迎合不影响用户”或“奉承不影响系统表现”，也不能宣称差异统计显著。各组很小，且同一文献可以有多个定义标签。

可直接使用的英文：

> Outcome coverage also differed across sycophancy labels: all four publications coded for hallucination agreement included system performance, while none included a user-related outcome. Conversely, none of the seven publications coded for obsequiousness included system performance. These patterns identify potential measurement gaps within the mapped corpus rather than demonstrating an absence of effects.

## 可作背景 finding：最常见的定义不限于事实性错误

Failure to challenge/trying to get along 有 17/31（54.8%），Bias Agreement 有 13/31（41.9%），Stance Change 有 8/31（25.8%），Obsequiousness 有 7/31（22.6%），Hallucination Agreement 有 4/31（12.9%）。

适合写成：

> Failure to challenge or going along with the user was the most frequently coded definition (17/31), followed by bias agreement (13/31), whereas hallucination agreement was coded in four publications.

这说明的是文献中的定义覆盖，不能写成这些行为在真实 LLM 中发生得最频繁。也不要把多个定义人数相加；定义可以重叠。

## 评估方式：先做编码核对，再讨论方法缺口

Human - Specialist 有 5 篇，Human - Authors 有 8 篇，AI - prompted 有 8 篇。三类并集为 19 篇，另 12/31（38.7%）在这一组完全没有标记。两篇同时标记 Human - Authors 和 AI - prompted。

因此，暂不把“专家参与很少”或“多数论文用 AI 评估”作为主 finding。只能说当前地图中 5 篇标记专家评估，同时明确 12 篇未标记的编码不完整性。第一组名称 Evaluation method 仍是暂定名称。

## 推荐给团队的英文综合段落

> Across the 31 mapped publications, failure to challenge or going along with the user was the most frequently coded definition of sycophancy (17/31), followed by bias agreement (13/31). Outcome coverage was uneven: system performance and user opinion were coded in 12 and 11 publications, respectively, whereas user performance appeared in only four. At the publication level, 15 papers included at least one user-related outcome and 12 included system performance, but only one was coded for both. Outcome coverage also varied by definition: all four hallucination-agreement publications included system performance, while none included user-related outcomes; no obsequiousness publication included system performance. Together, these descriptive patterns motivate evaluations that connect system-level measures to user outcomes, particularly task performance. They characterize the current corpus and coding, rather than the prevalence, direction, or magnitude of sycophancy's effects.

篇幅紧时优先用前两个 findings，再选第三个中的一组清晰对照。初次讨论应同时展示计数依据和局限，而不是把所有零格都包装成独立贡献。

## 解释边界与可复核材料

- 当前 CSV 没有提供完整检索策略、纳入标准、筛选日志或编码一致性结果，因此使用“mapped corpus / included publications”，不称其覆盖整个研究领域。
- 每行都是一篇文献，包含综述类文献，不能把计数等同于独立实证证据量；会议短文、长文等也未加权。
- 标记表示纳入该属性，不表示某效应被证明、方向为正/负、效应大或有统计显著性。
- 空白是“未标记”，不能自动理解为“明确没有”；0 是当前编码中的零覆盖，不是全球研究空白。
- 热图颜色使用全样本分母 31；本文件的条件比例另外计算并明确写出分母。颜色不是效应量。
- Crossref 核对的是 DOI 及书目信息，没有用论文全文重新核实所有属性编码。对拟强调的零覆盖及唯一联合覆盖论文，建议团队再核对原文与编码。
- `output/final_map/findings_evidence.json` 包含每项统计的 DOI 列表与输入 SHA-256；`findings_counts.csv` 为计数表；`crossref_audit.csv` 为书目信息核对表。

复算：`python analyze_map.py "data/lit-map 2026s sycophancy - FINAL MAP.csv"`。
