---
title: Academic PPT v2
status: needs-triage
issue_tracker_status: local-only
---

# Academic PPT v2 PRD

## Problem Statement

工科学生需要把论文、学位论文、项目书、实验记录、调查数据、旧 PPT、图片、表格和公式转化为符合开题、中期、毕业答辩、组会、项目申报及会议报告要求的科研 PPT。现有 Skill 已具备场景规则、证据台账、模板解析、PPTX 克隆渲染和基础 QA，但规范与执行之间存在明显断层：素材解析主要停留在 PDF 内嵌图片，模板组件未形成可执行能力图，页面合同不会自动编译为合理布局，补充图表没有完整生产闭环，页面审核偏重文件结构而无法证明内容、证据、布局和视觉是否合理。

实际成品因此容易出现以下问题：内容被强行塞入少数多栏模板；组合对象、框线结构和位图占位框无法可靠处理；科研图表过小；空置卡片与无意义留白残留；计划的补充图表未被使用；Agent 可以绕过用户确认阶段；模板风格与自由页面不统一；用户手工修改后的 PPT 在再次生成时可能被覆盖。

用户需要的不是一个机械套版工具，也不是 CyberPPT 咨询风格的复制品，而是一个面向科研场景、证据可追溯、布局可解释、风格统一、自动化程度高且按风险控制流程重量的 PPT 生产系统。

## Solution

构建统一的 **V2 Core**，将多源素材理解、**Presentation Scene**、可组合的 **Research Method Profile**、证据建模、**Scientific Page Contract**、模板能力分析、布局编译、视觉任务生产、四层 QA、阶段确认、局部修订和三层交付连接成一个可恢复、可审计的工作流。

V2 以科研论证和可读性为最高优先级。模板通过 **Native Reuse**、**Reconstructive Reuse** 和 **Scientific Freeform** 三种模式使用；三种模式都必须保持统一的 **Deck Visual System**，但不得破坏 **Scientific Color Semantics**。

系统自动识别一个主要及若干辅助 **Research Method Profile**，第一版支持计算与模型、实验室实验、调查与统计、工程系统、文献与证据综合，并允许同一套 PPT 在页面级组合多个画像。**Presentation Scene** 决定汇报必须证明什么，方法画像决定什么算作证据、应该使用什么视觉载体以及如何审核。

系统采用 **Guided Workflow** 与 **Autonomous Draft** 两种交互方式，并独立选择 Lean、Standard 或 Strict **Rigor Profile**。正式交付必须经过用户确认；自动模式只能生成内部 QA 通过但未获用户批准的草稿。

最终系统必须能够证明 PPT 合理，但不在每页显示内部审核或强制参考文献。证明材料通过 **Evidence Provenance**、**Deck Rationale**、QA 报告及真实渲染结果保存在页面外。

## User Stories

1. 作为工科学生，我希望系统自动识别我的汇报场景，从而不必理解内部场景分类。
2. 作为工科学生，我希望系统区分开题、中期、毕业答辩和组会，从而生成符合不同评审目标的论证结构。
3. 作为组会汇报者，我希望系统区分文献精读、周报进展和课题进展，从而不把所有组会做成缩短版答辩。
4. 作为项目负责人，我希望系统支持项目申报、比赛、中期和结题，从而按指标、证据和交付要求组织内容。
5. 作为会议报告人，我希望系统按会议时长保留最强证据，从而避免把完整论文压缩成小字号页面。
6. 作为用户，我希望系统自动推断研究方法画像并展示依据，从而只需确认而无需手工分类。
7. 作为交叉研究项目成员，我希望一套 PPT 可以组合多个研究方法画像，从而正确表达模型、实验和工程实现。
8. 作为算法研究者，我希望页面覆盖数据集、基线、指标、消融、泛化和误差，从而证明模型结论可信。
9. 作为实验研究者，我希望页面覆盖样本、对照、实验条件、重复和统计解释，从而避免只展示漂亮结果图。
10. 作为调查研究者，我希望页面覆盖总体、样本、量表、信效度、偏差和统计模型，从而正确解释调查结论。
11. 作为工程系统研究者，我希望页面覆盖需求、架构、实现、测试环境、性能和可靠性，从而形成工程验证闭环。
12. 作为文献精读汇报者，我希望系统区分作者结论、我的解释和后续研究计划，从而不误述论文。
13. 作为用户，我希望系统盘点工作区内的明显材料，从而不必重复提供已经存在的文件路径。
14. 作为用户，我希望系统识别每份材料的角色，从而区分任务约束、主要证据、增量证据、历史表达、视觉素材和模板。
15. 作为用户，我希望同一个 PPTX 可以同时提供历史内容、视觉素材和模板参考，从而不被错误地归为单一角色。
16. 作为用户，我希望系统解析 PDF 的正文、图、表、公式区域和精确页码，从而建立可靠来源定位。
17. 作为用户，我希望系统解析 DOCX 的标题、段落、表格、图片、题注和 OMML 公式，从而保留原生结构。
18. 作为用户，我希望系统解析 PPTX 的文本、图片、表格、图表、组合对象、备注和页面关系，从而复用既有表达。
19. 作为用户，我希望系统解析 XLSX/CSV 的工作表、表头、单位、范围、公式值和缺失值，从而可靠重绘图表。
20. 作为用户，我希望系统为每个输入文件记录哈希、版本、角色和解析状态，从而支持恢复与变更检测。
21. 作为研究者，我希望每条主张能够追溯到具体页、段落、幻灯片 shape 或单元格范围，从而证明内容有据可查。
22. 作为研究者，我希望系统保留事实、方法、结果、限制和解释之间的区别，从而避免把推断写成事实。
23. 作为研究者，我希望系统检测不同材料中的数字、单位、状态和解释冲突，从而避免静默选择错误来源。
24. 作为用户，我希望阻断冲突立即由我裁决，从而不让错误结论进入故事线。
25. 作为用户，我希望重要冲突在 Phase 1 集中展示，从而避免被细小问题频繁打断。
26. 作为用户，我希望非阻断差异按来源策略自动处理并留痕，从而保持流程高效。
27. 作为用户，我希望来源优先级根据场景、目标和我的明确要求按主张确定，从而不使用僵硬的全局排序。
28. 作为研究者，我希望默认只进行单位换算、排序、比例和图表重绘等 Presentation Transform，从而避免系统擅自重新分析数据。
29. 作为研究者，我希望 Derived Analysis 必须经过明确授权并可复现，从而区分系统计算与源材料结果。
30. 作为研究者，我希望系统计算与原报告不一致时形成阻断冲突，从而防止错误数字被掩盖。
31. 作为用户，我希望在生成大纲前看到 2–3 条有证据支持的候选故事线，从而选择最适合受众的表达路径。
32. 作为用户，我希望页面规划以问题和主张为中心，而不是照搬论文目录，从而形成可讲述的论证。
33. 作为用户，我希望每页明确主张、证据、视觉载体、解释或边界及转场，从而保证页面具有完整作用。
34. 作为用户，我希望页面信息密度按证据与关系衡量，而不是按字符数衡量，从而避免文字堆积。
35. 作为用户，我希望系统在组装前展示完整逐页 PRD，从而确认页数、顺序、内容、视觉和时间。
36. 作为用户，我希望修改板块、页面或结论后只使相关下游产物失效，从而避免整套重做。
37. 作为用户，我希望系统分析模板的字体、色板、标题、导航、网格、卡片、图表和装饰身份，从而保持全篇统一风格。
38. 作为用户，我希望系统识别原生文本、图片槽、表格和图表，从而直接复用可编辑组件。
39. 作为用户，我希望系统把图标、标题、正文和外框识别为复合组件，从而整体移动或删除而不破坏关系。
40. 作为用户，我希望系统识别没有真正 group 但视觉上属于同一模块的 shape，从而处理多框线页面。
41. 作为用户，我希望组合对象默认作为整体处理并按需暴露子槽，从而避免无意义拆散。
42. 作为用户，我希望系统区分可替换位图、位图视觉基底和位图语义组件，从而选择保留、替换、重建或弃用。
43. 作为用户，我希望包含样例文字和占位框的位图区域被重建而不是简单遮盖，从而避免残留和图层破坏。
44. 作为用户，我希望完全不可用的模板页被拒绝，从而不为模板忠实度牺牲内容质量。
45. 作为用户，我希望布局编译器根据页面角色、关系、组件数、图像数和容量选择模板页，从而减少人工 shape 绑定。
46. 作为用户，我希望布局候选先通过容量、可读性、样例残留和关系匹配硬过滤，从而避免错误布局进入渲染。
47. 作为用户，我希望系统优先选择原生复用最多、修改最少且证据空间合理的布局，从而兼顾稳定性和表达质量。
48. 作为用户，我希望轻微容量差异通过移动、缩放、重排或隐藏原生组件处理，从而实现 Template Adaptive 行为。
49. 作为用户，我希望没有兼容模板页时进入 Reconstructive Reuse，从而保留 Template Identity 而不强塞内容。
50. 作为用户，我希望 Scientific Freeform 只在原生与重建模式都无法表达论证时使用，从而控制风格漂移。
51. 作为用户，我希望布局方案在组装前展示源页、复用模式、组件关系、删除与重建内容及风险，从而能够裁决。
52. 作为用户，我希望标题、正文、关键数字、科学标签和简单结构保持可编辑，从而能够进行常规修改。
53. 作为用户，我希望复杂统计图、公式、地图、显微图和科研示意图可以使用高质量图片或 SVG，从而不为完全可编辑牺牲质量。
54. 作为用户，我希望主要信息层不会被整页图片压平，从而保持 PPTX 的基本可编辑性。
55. 作为用户，我希望系统在页面规划阶段发现视觉缺口，从而不是渲染后才用装饰图填空。
56. 作为用户，我希望每个视觉任务记录要证明的主张、证据、科学语义、编辑要求和所需面积，从而可审核地生成。
57. 作为用户，我希望原始科研图能够被裁切、清理、放大并配套解读，从而真正支持页面主张。
58. 作为用户，我希望数值结果能够从已验证数据重绘为图表，从而提高可读性而不发明数据。
59. 作为用户，我希望流程、架构和因果链优先生成原生可编辑图形，从而保持结构清晰。
60. 作为用户，我希望表格、公式和复杂视觉使用合适后端，从而避免所有视觉退化为图片或项目符号。
61. 作为用户，我希望视觉任务经历 planned、locked、rendered、bound、inspected 和 accepted 状态，从而不会生成后被遗忘。
62. 作为用户，我希望未使用视觉必须被拒绝、替换或豁免并说明原因，从而提高补充图表利用率。
63. 作为用户，我希望全篇共享同一 Deck Visual System，从而让原生页、重建页和自由页看起来属于同一套 PPT。
64. 作为用户，我希望统一风格不等于重复同一版式，从而根据内容使用图文、流程、对比、结果、表格和公式页面。
65. 作为研究者，我希望 Scientific Color Semantics 优先于模板配色，从而不破坏热力图、类别图例、影像通道或地图含义。
66. 作为用户，我希望来源图保持必要原色，但外围标题、标注和解释遵循统一风格，从而兼顾科学性和一致性。
67. 作为用户，我希望系统执行结构、科学语义、视觉构图和用户四层审核，从而不仅证明 PPTX 文件没有损坏。
68. 作为用户，我希望系统检查溢出、重叠、字号、有效分辨率、样例残留和空置组件，从而消除基础质量问题。
69. 作为研究者，我希望审核图表是否真的支持标题主张，从而避免相关但无证明作用的视觉。
70. 作为用户，我希望审核阅读顺序、视觉焦点、信息密度和连续页面重复，从而提升整体讲述质量。
71. 作为用户，我希望页面按科学重要性、来源风险、布局重建和视觉复杂度分级，从而集中审核高风险页面。
72. 作为用户，我希望自动返工先调整布局、再更换模板页或拆页，并限制轮次，从而避免无限缩字和循环失败。
73. 作为用户，我希望默认统一确认完整方案并详细验收代表页和高风险页，从而兼顾效率和质量。
74. 作为高保真用户，我希望可以切换逐页制作与逐页确认，从而获得更强控制。
75. 作为用户，我希望每个阶段明确展示检查内容、关键决定、风险、产物和一个确认请求，从而知道系统正在做什么。
76. 作为用户，我希望系统区分 validated、confirmed 和 auto_approved，从而不把内部校验冒充我的批准。
77. 作为用户，我希望 Autonomous Draft 不暂停但仍生成全部内部产物和 QA，从而快速获得完整草稿。
78. 作为用户，我希望未确认的自动草稿不能进入正式交付层，从而避免误用。
79. 作为用户，我希望 Lean、Standard 和 Strict 根据场景与风险自动推荐，从而不让简单周报走最重流程。
80. 作为用户，我希望交互模式与 Rigor Profile 独立选择，从而可以自动生成严格草稿或引导生成轻量周报。
81. 作为用户，我希望跨会话读取 workflow state 并从最早 stale 阶段恢复，从而不重复已经确认的工作。
82. 作为用户，我希望源材料、模板、数字或措辞变化只使相关阶段和页面失效，从而提高迭代效率。
83. 作为用户，我希望默认获得 Concise Speaker Notes，从而把讲解顺序、边界和转场放到备注而不是塞进页面。
84. 作为用户，我希望逐字稿和 anticipated questions 作为可选产物，从而按场景决定是否需要。
85. 作为用户，我希望系统内部保留 Evidence Provenance 而不强制每页显示参考文献，从而保持页面干净。
86. 作为用户，我希望版权、直接转载、学校要求或明确请求时才显示可见引用，从而满足必要规范。
87. 作为用户，我希望获得 Deck Rationale，从而知道每页为何存在、证据为何足够、视觉和布局为何合理。
88. 作为用户，我希望 QA 说明位于页面外，从而不在 PPT 中出现内部生产术语。
89. 作为用户，我希望 PowerPoint 默认为 Authoritative Runtime，从而以真实 Windows 渲染验收。
90. 作为 WPS 用户，我希望可以在 Phase 0 将 WPS 设为权威环境，从而按实际使用软件优化。
91. 作为跨平台用户，我希望 portable 模式采用保守字体与对象，从而提高兼容性。
92. 作为用户，我希望字体在布局前完成盘点、替代和容量重测，从而避免最终渲染才出现换行错误。
93. 作为用户，我希望正式交付至少完成一个权威环境的真实渲染，从而不把包结构检查当作视觉验收。
94. 作为研究者，我希望原始材料默认在本地处理，从而保护未发表内容和实验数据。
95. 作为用户，我希望外部发送原始材料或未公开内容前必须单独确认，从而掌握隐私风险。
96. 作为用户，我希望公开信息检索和抽象的非敏感生成提示可以使用外部服务并留痕，从而兼顾能力与隐私。
97. 作为用户，我希望最终 Delivery Bundle 分为 deliverables、audit 和 working，从而既易用又可追溯。
98. 作为用户，我希望默认交付 PPTX、contact sheet、单页 PNG、Deck Rationale 和质量摘要，从而便于使用和审阅。
99. 作为用户，我希望审计 JSON 不堆在可见交付层，从而保持交付简洁。
100. 作为用户，我希望工作临时资产不会被正式 PPT 引用到项目外部，从而避免移动后资源丢失。
101. 作为用户，我希望交付文件使用时间戳而不是混乱的 final_v2 命名，从而识别正式版本。
102. 作为用户，我希望用户编辑后的生成 PPTX 可以成为 Authoritative Edit Baseline，从而继续局部修改。
103. 作为用户，我希望未指定页面和检测到的手工对象受到保护，从而不被全量重建覆盖。
104. 作为用户，我希望重建手工修改页前看到会丢失的内容，从而能够裁决。
105. 作为用户，我希望第一版支持局部修改但不假装能够完成复杂三方语义合并，从而获得可预期行为。
106. 作为现有用户，我希望旧命令和受支持的 v1 产物仍能通过兼容层运行，从而平滑迁移。
107. 作为维护者，我希望新项目统一进入 V2 Core，从而不继续扩展松散 v1 合同。
108. 作为维护者，我希望现有渲染、克隆、导出和基础验证能力被复用，从而避免无价值重写。
109. 作为维护者，我希望 8 个 Core Benchmark Suite 案例作为发布基准，从而防止优化一个场景破坏另一个场景。
110. 作为维护者，我希望快速结构测试在每次修改运行，完整端到端与模板压力测试按风险运行，从而平衡反馈速度和覆盖率。

## Implementation Decisions

- 建立统一 **V2 Core**，包含 Workflow Orchestrator、Source Ingestion、Evidence Graph、Scene and Method Profile Resolver、Page Contract Planner、Template Capability Graph、Layout Compiler、Visual Task Pipeline、Deck Style Manager、Rendering Runtime Adapter、QA Engine、Revision Baseline Manager、Delivery Builder 和 Legacy Compatibility Adapter。
- 主 Skill 保持轻量，只负责发现输入、选择 Presentation Scene、推断 Research Method Profile、推荐 Rigor Profile、展示阶段状态、请求必要确认并路由到深模块。
- Workflow Orchestrator 是阶段状态的唯一写入口。阶段状态为 `not_started`、`draft`、`awaiting_confirmation`、`confirmed`、`stale` 或 `failed`，并记录输入/输出哈希、依赖、确认说明和影响页面。
- `validated` 表示内部校验，`confirmed` 只表示用户明确确认，`auto_approved` 只允许 Autonomous Draft 继续执行。
- Guided Workflow 可以形成正式交付；Autonomous Draft 只能形成未确认草稿。
- Rigor Profile 与交互模式独立。Lean 用于短、低风险任务；Standard 用于正式科研汇报；Strict 由高保真、多冲突、Derived Analysis、敏感数据、复杂模板或重复 QA 失败触发。
- Source Ingestion 将 PDF、DOCX、PPTX、XLSX/CSV、图片和文本转换为统一 Source 模型，并保留精确位置与不可变哈希。
- Evidence Graph 对事实、方法、参数、实验、结果、限制、解释和资产建立稳定 ID，并提供 Source → Evidence → Claim → Page → Visual 的追踪链。
- Evidence Authority Policy 按主张与证据族应用，不设置“最新文件”或“论文”全局优先规则。
- Evidence Conflict 分为 blocking、material 和 non-blocking。blocking 立即裁决，material 在 Phase 1 批量确认，non-blocking 自动处理并记录。
- Presentation Transform 默认允许并记录公式；Derived Analysis 需要显式授权、可复现记录和系统计算标签。
- Presentation Scene 与 Research Method Profile 正交。一个 deck 只有一个主要场景，但可包含多个方法画像，并在页面级记录适用画像及 proof requirements。
- 第一版方法画像为 computational modeling、laboratory experiment、survey empirical analysis、engineering system validation 和 literature synthesis。
- Scientific Page Contract 是页面规划与布局编译的统一输入，至少包含页面问题、主张、证据、证据载体、解释/边界、关系、模块数、最小可读尺寸、时间、前后承接和方法画像。
- Template Capability Graph 同时使用 OOXML/PPTX 对象信息和真实页面预览，表达原生原子组件、原生复合组件、几何关联组件、可替换位图、位图视觉基底、位图语义组件及其父子、包含、对齐、重复和连接关系。
- 组合对象默认作为整体能力处理；仅在绑定内部文字、图片或子模块时暴露子对象。
- 位图 OCR/视觉分析用于理解而非假装恢复编辑性。含样例文字或占位框的位图语义组件应重建或拒绝，不默认使用遮罩覆盖。
- Layout Compiler 先执行关系、容量、最小字号、图表尺寸、样例残留和组件利用率硬过滤，再按 Native Reuse、修改成本、证据空间、Template Identity 和构图多样性排序。
- Native Reuse、Reconstructive Reuse 和 Scientific Freeform 是正式渲染模式。Scientific Page Contract 的论证质量和可读性高于模板几何复刻。
- Reconstructive Reuse 使用统一 Deck Visual System 重建可编辑组合；Scientific Freeform 需要记录无兼容原生或重建方案的原因。
- Deck Visual System 在视觉确认后锁定字体、色板、标题/导航几何、间距、卡片、图标、图表、表格、页脚和装饰身份。统一风格不要求页面布局相同。
- Scientific Color Semantics 不得为了 Deck Visual System 被任意重映射。源图可保留必要原色，外围容器、标题和解读遵循统一风格。
- Editable Information Layer 包括标题、正文、关键数字、科学标签和简单表格/图表/结构；Complex Visual Asset 可以使用高质量 bitmap 或 SVG，但不能压平完整页面信息层。
- Visual Task 是可持久化状态机，至少经历 planned、semantics_locked、rendered、bound_to_slide、render_inspected 和 accepted；失败进入 rework、replace、split、reject 或 waive。
- 视觉后端按任务类型路由：源图清理、matplotlib/native chart、native table、native diagram、equation rendering、licensed web image 或 approved generation。
- 所有生成视觉必须绑定 Scientific Page Contract 和 Evidence ID；生成图不能提供科学数字、标签或关系事实。
- QA Engine 分为结构 QA、科学语义 QA、视觉构图 QA 和用户审核。硬门槛不能被总分抵消。
- 页面风险来自科学重要性、来源不确定性、重建模式、视觉复杂度、容量压力及 QA 置信度。Risk-Driven Review 默认审核代表页与全部高风险页。
- 自动返工最多两轮：先调整组件和图文比例，再允许更换布局、重建或拆页；仍失败则请求用户裁决。
- Deck Rationale 默认解释每页作用、证据、视觉策略、布局理由、风险和 QA 结果，但不写进 PPT 页面。
- Evidence Provenance 默认内部保存；可见引用仅由许可、直接外部复用、场景、机构规则或用户要求触发。
- Concise Speaker Notes 默认包含讲解顺序、中心解释、重要边界、转场和建议时间；逐字稿和 anticipated questions 为可选。
- Authoritative Runtime 默认为 Windows PowerPoint；用户可在 Phase 0 选择 WPS；portable 为显式保守模式。正式视觉验收必须使用权威运行环境真实渲染。
- 字体在布局前完成盘点、缺失处理和容量重测；商业字体不默认嵌入。
- Local-First Processing 是默认隐私策略。外部发送用户原始材料、数据、页面截图或未公开内容需要单独授权并写入外部处理日志。
- Delivery Bundle 使用 deliverables、audit、working 三层。产物按 Rigor Profile 惰性创建，避免简单任务生成完整严格审计集。
- Authoritative Edit Baseline 支持用户编辑后的 PPTX 回流。未指定页面与检测到的手工对象默认受保护；第一版不承诺完整双向语义同步和复杂三方合并。
- V2 Core 是新项目的唯一内部模型。旧命令和明确支持的 v1 artifact 通过 Legacy Compatibility Adapter 转换，并由回归测试覆盖。
- 默认不使用动画；自动应用可读对比度与色盲友好检查，但不得改写 Scientific Color Semantics。

## Testing Decisions

- 测试只验证模块的外部行为、状态转换、输入输出合同和真实渲染结果，不锁定私有函数、启发式实现或中间调用顺序。
- 先为现有脚本建立 characterization tests，固定当前可复用的页面克隆、shape 绑定、图片替换、导出和包完整性行为。
- Source Ingestion 需要格式级 fixtures，验证文本、图、表、公式、题注、组合对象、单元格范围、单位和来源定位。
- Evidence Graph 需要测试来源追踪、冲突分级、权限策略、Presentation Transform、Derived Analysis 授权和选择性失效传播。
- Scene and Method Profile Resolver 需要测试单一画像、混合画像、置信依据、用户覆盖和 proof requirements。
- Template Capability Graph 需要覆盖原生 group、未 group 的视觉组件、嵌套图片、位图 scaffold、位图文字、原生表格、图表、连接线、SmartArt、高层级 z-order、顶部/侧边/无导航、4:3 和 16:9。
- Layout Compiler 测试使用 Scientific Page Contract 作为输入，验证硬过滤、候选排序、Native/Reconstructive/Freeform 决策、容量和多样性，不断言具体内部打分实现。
- Visual Task Pipeline 测试每种状态转换、证据绑定、输出存在、最终使用、拒绝/豁免理由和不可静默降级规则。
- QA Engine 测试结构硬门槛、场景/方法画像 proof requirements、图表主张一致性、风险分级、两轮返工和失败升级。
- Workflow Orchestrator 测试非法跳转、确认权、Autonomous Draft、哈希变更、选择性失效、跨会话恢复及正式交付门。
- Revision Baseline Manager 测试页面新增/删除/换序、手工文本和几何变化检测、未指定页面保护、局部修改和重建披露。
- Rendering Runtime Adapter 至少在 Windows PowerPoint 完成真实渲染回归；WPS 目标案例必须在 WPS 验证。无权威运行环境时测试必须明确标记未完成视觉验收。
- Delivery Builder 测试 deliverables/audit/working 隔离、资源自包含、版本哈希一致、未确认草稿隔离和临时文件不泄漏。
- Core Benchmark Suite 包含八个固定端到端案例：计算模型毕业答辩、实验室实验中期、调查统计开题、工程系统项目申报、文献精读组会、混合方法工程项目、周报进展组会、课题进展组会。
- 六份根目录 PPTX 是 Reference Corpus 和压力素材，不作为统一视觉金标准；页面级正例、可借鉴例和反例需分别标注。
- 八个内置模板进入跨模板回归；模板家族色彩变体允许共享几何，但必须保留可识别身份。
- 每次修改运行快速结构测试；修改解析、布局、渲染或 QA 时运行相关端到端案例；发布与新增模板时运行完整 Core Benchmark Suite 和模板压力集。
- 正式交付硬门槛包括：伪造事实为零、未处理 blocking conflict 为零、必需论证遗漏为零、溢出/明显遮挡为零、样例残留为零、未审核复杂视觉为零、未处置视觉任务为零、未经授权 Derived Analysis 为零、权威运行环境真实渲染通过。
- 质量向量分别记录 Evidence Provenance、科学论证完整性、视觉载体可读性、内容布局匹配、信息层级、Template Identity、构图多样性和修改稳定性，不压缩为可掩盖硬失败的单一分数。

## Out of Scope

- 第一版不支持所有学科的专属知识模型；按证据生产方式支持五类 Research Method Profile。
- 第一版不执行未经用户授权的新统计检验、回归、模型训练或科学推断。
- 第一版不保证所有复杂统计图、公式、地图、显微图和科研示意图对象级可编辑。
- 第一版不保证 PowerPoint、WPS 和 LibreOffice 像素级一致，只保证选定 Authoritative Runtime 的正式验收。
- 第一版不提供复杂用户编辑与旧自动状态之间的完整双向语义同步或三方对象合并。
- 第一版不自动理解用户新增任意图形的科学语义。
- 第一版不默认使用动画、复杂转场或软件特有交互效果。
- 第一版不把所有 Reference Corpus 页面视为质量真值，也不直接复制 CyberPPT 的视觉风格或 ImageGen 工作流。
- 第一版不穷举所有 Presentation Scene、Research Method Profile 和模板的笛卡尔组合测试。
- 第一版不默认上传原始材料、实验数据或未公开内容到外部服务。
- 第一版不强制在每页显示参考文献、来源或内部 QA 说明。

## Further Notes

- 本 PRD 使用项目领域词汇，并遵循“Build a v2 core behind legacy-compatible entry points”架构决策。
- 推荐实施顺序：建立八个端到端基准与 characterization tests；统一 schema 与 workflow state；构建 Source Ingestion 与 Evidence Graph；构建 Template Capability Graph；实现 Layout Compiler；完成 Visual Task Pipeline；接入四层 QA；实现 Revision Baseline Manager 与 Delivery Builder；最后收敛 Legacy Compatibility Adapter。
- 采用纵向切片实施，每个里程碑至少完成一个真实场景从输入到可渲染页面的闭环，避免先建设大量孤立 schema 而长期无法验证成品。
- 当前目录没有项目级 issue tracker 配置，且环境没有 GitHub CLI；本 PRD 因此以 `needs-triage` 状态保存在项目内，尚未发布为 GitHub Issue。
