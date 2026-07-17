from academic_ppt.autobuild import CompleteContentCompiler, EvidencePassage
from academic_ppt.evidence import EvidenceNode


def _evidence_node(evidence_id: str, evidence_type: str, text: str, page: int) -> EvidenceNode:
    return EvidenceNode(evidence_id, evidence_type, text, "SRC", evidence_id, {"page": page}, {})


def test_english_evidence_excerpts_stop_at_clause_or_word_boundaries():
    text = (
        "Agriculture is the foundation of the national economy; thus, promoting steady "
        "agricultural development and safeguarding food security is paramount."
    )
    passage = EvidencePassage((), text, 2)

    title = CompleteContentCompiler._title(text, "research_problem", 1, 8)
    claim = CompleteContentCompiler._claim(text)
    evidence_line = CompleteContentCompiler._evidence_line(passage)
    interpretation = CompleteContentCompiler._interpretation(passage, 1, 8)
    chunks = CompleteContentCompiler._split_claim(claim, 3)

    assert title == "核心问题：Agriculture is the foundation of the national economy"
    assert claim == "Agriculture is the foundation of the national economy"
    assert evidence_line.endswith("thus, promoting steady agricultural development and safeguarding")
    assert interpretation.endswith(
        "thus, promoting steady agricultural development and safeguarding food security is paramount"
    )
    assert " ".join(chunks) == claim


def test_title_removes_leading_parenthetical_citation_before_clipping():
    text = (
        "(Mumuni and Mumuni, 2025). The resulting CSV files contain two columns "
        "and conform to the Crop GraphRAG design."
    )

    title = CompleteContentCompiler._title(text, "method", 2, 8)

    assert title.startswith("核心方法：The resulting CSV files contain two columns")
    assert "Mumuni" not in title


def test_titles_do_not_end_with_dangling_english_connectors():
    text = (
        "Intelligent prevention and control of crop diseases and pests is a critical link "
        "in safeguarding food security."
    )

    title = CompleteContentCompiler._title(text, "results", 4, 8)

    assert title == "关键结果：Intelligent prevention and control of crop diseases and pests"


def test_bibliography_entries_are_not_selected_as_evidence_passages():
    text = (
        "Chen, J., Liu, Z., Huang, X., Wu, C., and Jiang, G. (2024). "
        "When large language models meet personalization: perspectives, challenges, and opportunities. "
        "World Wide Web 27, 42. doi:10.1000/example"
    )

    assert not CompleteContentCompiler._passage_is_usable(EvidencePassage((), text, 12))


def test_table_and_figure_captions_are_not_used_as_narrative_claims():
    table = EvidencePassage((), "TABLE 3 Detailed results of ablation experiments. Method Accuracy Recall F1 score.", 11)
    figure = EvidencePassage((), "FIGURE 7 Comparative results with statistical significance and confidence intervals.", 12)

    assert not CompleteContentCompiler._passage_is_usable(table)
    assert not CompleteContentCompiler._passage_is_usable(figure)


def test_numbered_english_section_heading_is_stripped_before_sentence_split():
    text = (
        "2.1.2 Element extraction\nAfter segmenting the structured data, we design a prompt "
        "engineering scheme for a large language model."
    )

    title = CompleteContentCompiler._title(text, "method", 3, 8)

    assert title == "核心方法：We design a prompt engineering scheme for a large language model"
    assert CompleteContentCompiler._claim(text).startswith("After segmenting the structured data")


def test_scene_contract_aliases_select_role_specific_result_sentence():
    text = (
        "By sequentially posing the evaluation questions, we conducted comparative analyses. "
        "Taken together, Table 3 and Figure 6 show that Crop GraphRAG delivers the best overall quality, "
        "with 89.4% accuracy and 86.7% recall."
    )
    passage = EvidencePassage((), text, 10)

    title = CompleteContentCompiler._title(text, "key_results", 4, 8)
    claim = CompleteContentCompiler._claim(text, "key_results")
    evidence_line = CompleteContentCompiler._evidence_line(passage, "key_results")

    assert title == "关键结果：Crop GraphRAG delivers the best overall quality"
    assert claim.startswith("Taken together, Table 3 and Figure 6 show that Crop GraphRAG")
    assert "89.4% accuracy" in claim
    assert "By sequentially posing" not in evidence_line


def test_limitation_role_prefers_explicit_constraint_sentence():
    text = (
        "Local query is an entity-centric retrieval strategy. "
        "Local querying is subject to constraints. "
        "If the entity is not clearly specified, imprecise retrieval can lead to inaccurate answers."
    )

    title = CompleteContentCompiler._title(text, "limitations", 6, 8)
    claim = CompleteContentCompiler._claim(text, "limitations")

    assert title == "局限与边界：Local querying is subject to constraints"
    assert claim.startswith("Local querying is subject to constraints")
    assert "inaccurate answers" in claim


def test_limitation_evidence_and_interpretation_advance_by_complete_sentences():
    text = (
        "Although the proposed framework demonstrates significant improvements over existing models, certain limitations remain. "
        "The response time in information retrieval could be further optimized to enhance real-time performance. "
        "The current framework focuses mainly on long-text processing and uses a single information modality."
    )
    passage = EvidencePassage((), text, 13)

    evidence_line = CompleteContentCompiler._evidence_line(passage, "limitations")
    interpretation = CompleteContentCompiler._interpretation(
        passage,
        6,
        8,
        focus="limitations",
        skip_evidence_excerpt=True,
    )

    assert evidence_line.endswith("optimized to enhance real-time performance")
    assert "current framework focuses mainly" in interpretation.casefold()
    assert "optimized to enhance" not in interpretation


def test_contribution_excerpt_does_not_end_on_an_english_possessive():
    text = (
        "We designed and implemented an innovative Crop GraphRAG framework that selects answering "
        "strategies according to the user’s query. The retrieval method is chosen dynamically by query type."
    )
    passage = EvidencePassage((), text, 13)

    claim = CompleteContentCompiler._claim(text, "contribution")
    interpretation = CompleteContentCompiler._interpretation(passage, 5, 8, focus="contribution")

    assert claim.endswith("according to the user’s query")
    assert not claim.endswith("user’s")
    assert interpretation.startswith("解读：The retrieval method is chosen dynamically")


def test_claim_can_advance_to_a_nearby_boundary_without_ignoring_an_earlier_semicolon():
    problem = (
        "Agricultural practitioners face fragmented information and low retrieval efficiency when seeking accurate "
        "actionable knowledge. General-purpose models can also hallucinate."
    )
    clause = (
        "Agriculture is the foundation of the national economy; thus, promoting steady agricultural development "
        "and safeguarding food security is paramount."
    )

    assert CompleteContentCompiler._claim(problem).endswith("actionable knowledge")
    assert CompleteContentCompiler._claim(clause) == "Agriculture is the foundation of the national economy"


def test_native_process_steps_are_complete_semantic_sentences():
    text = (
        "We designed and implemented an innovative Crop GraphRAG framework that selects answering strategies according to the user’s query. "
        "For factual questions, the system performs entity-centric local querying to locate information precisely. "
        "For analytical questions, it applies global querying with community summaries. "
        "These two modes ensure flexibility across diverse scenarios. "
        "We comprehensively validated the effectiveness of the system through experiments."
    )

    steps = CompleteContentCompiler._process_steps(
        text,
        "contribution",
        "We designed Crop GraphRAG",
        "解读：The framework adapts retrieval by query type",
        "下一页转向局限",
    )

    assert len(steps) == 5
    assert all(len(step.split()) >= 6 for step in steps)
    assert all(len(step) <= 120 for step in steps)
    assert any("validated" in step for step in steps)

    result_steps = CompleteContentCompiler._process_steps(
        "We designed a framework. Results on the evaluation dataset show that the proposed framework clearly "
        "outperforms conventional frameworks and retrieval methods across multiple dimensions.",
        "contribution",
        "We designed a framework",
        "解读：The evaluation confirms the contribution",
        "下一页",
    )
    assert any(step.endswith("retrieval methods") for step in result_steps)


def test_interpretation_prefers_complete_sentence_and_labels_metric_continuation():
    truncated_block = EvidencePassage(
        (),
        "We evaluated all methods across five randomized replications, yielding paired observations. We tested whether Crop",
        10,
    )
    result = EvidencePassage(
        (),
        "Eliminating the Knowledge Graph reduces performance to 84.1% accuracy and 80.5% recall, yet it still "
        "outperforms naive RAG, which attains 72.6% accuracy, 68.3% recall, and a BLEU score of 0.41.",
        10,
    )

    truncated_detail = CompleteContentCompiler._interpretation(truncated_block, 3, 8, focus="experiment_setup")
    result_detail = CompleteContentCompiler._interpretation(result, 4, 8, focus="key_results")

    assert truncated_detail.endswith("yielding paired observations")
    assert "We tested whether Crop" not in truncated_detail
    assert "referenced baseline" in result_detail


def test_experiment_title_uses_complete_comparison_topic_before_long_method_clause():
    text = (
        "For both the ablation and comparative experiments, we evaluated all methods on the same set of questions "
        "across five randomized replications."
    )

    title = CompleteContentCompiler._title(text, "experiment_setup", 3, 8)

    assert title == "实验设计：For both the ablation and comparative experiments"


def test_focus_selection_prefers_research_contribution_over_metric_formula_wording():
    formula_text = (
        "The weights are uniform, implying equal contribution from each n-gram order. "
        "The brevity penalty is adjusted for specific evaluation tasks."
    )
    findings_text = (
        "We constructed a domain-specific knowledge graph for crop diseases and pests. "
        "We designed and implemented Crop GraphRAG and validated its effectiveness through experiments."
    )
    formula = EvidencePassage((_evidence_node("E1", "method", formula_text, 9),), formula_text, 9)
    findings = EvidencePassage((_evidence_node("E2", "result", findings_text, 13),), findings_text, 13)

    selected = CompleteContentCompiler._select_for_focus([formula, findings], ("contribution",))

    assert selected == [findings]


def test_focus_selection_prefers_explicit_limitation_evidence_over_generic_tradeoff():
    tradeoff_text = (
        "Latency ranges from 3.2 to 4.5 seconds, indicating an acceptable trade-off between quality and efficiency."
    )
    limitation_text = (
        "Certain limitations remain. The response time could be optimized, and the current framework uses a single modality."
    )
    tradeoff = EvidencePassage((_evidence_node("E1", "result", tradeoff_text, 10),), tradeoff_text, 10)
    limitation = EvidencePassage((_evidence_node("E2", "limitation", limitation_text, 13),), limitation_text, 13)

    selected = CompleteContentCompiler._select_for_focus([tradeoff, limitation], ("limitations",))

    assert selected == [limitation]


def test_terminal_pages_do_not_consume_source_figures():
    figures = [{"path": "figure-1.png", "source_page": 1}]

    assert CompleteContentCompiler._page_figure(figures, 1, 0, 8) is None
    assert len(figures) == 1
    assert CompleteContentCompiler._page_figure(figures, 1, 1, 8)["path"] == "figure-1.png"
    assert not figures


def test_contribution_page_rejects_unrelated_adjacent_metric_figure():
    figures = [{"path": "metrics.png", "source_page": 12, "caption": "Comparative experiment scoring"}]

    selected = CompleteContentCompiler._page_figure(
        figures,
        13,
        5,
        8,
        focus="contribution",
        claim="We designed and implemented a dynamic query framework",
    )

    assert selected is None
    assert len(figures) == 1


def test_interpretation_can_advance_past_the_visible_evidence_excerpt():
    text = (
        "A complete claim occupies the first evidence segment and establishes the baseline result. "
        "The visible evidence excerpt adds a reproducible measurement and its source location. "
        "The interpretation then explains why the measurement changes the decision boundary."
    )
    passage = EvidencePassage((), text, 4)
    evidence_line = CompleteContentCompiler._evidence_line(passage)
    interpretation = CompleteContentCompiler._interpretation(
        passage,
        3,
        8,
        skip_evidence_excerpt=True,
    )

    assert interpretation.removeprefix("解读：") not in evidence_line
