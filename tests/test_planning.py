import tempfile
import unittest
from pathlib import Path

from academic_ppt.evidence import EvidenceGraph
from academic_ppt.ingest import SourceIngestor
from academic_ppt.planning import PageDraft, PagePlan, PagePlanner
from academic_ppt.scenes import ScenePlanContract


class PagePlannerTests(unittest.TestCase):
    def test_builds_evidence_bound_scientific_page_contract_and_reviewable_prd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "结果.md"
            source_path.write_text("模型 F1 为 92.9%。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(source_path)])
            evidence = graph.all()[0]
            claim = graph.add_claim("模型在测试中达到 92.9 F1。", [evidence.evidence_id])
            draft = PageDraft(
                page_id="P001",
                section="实验与结果",
                title="模型在测试中达到 92.9 F1",
                question_answered="实验结果是否支持模型有效性？",
                claim_id=claim.claim_id,
                interpretation="该结果支持模型有效性，但需要结合数据集边界解释。",
                next_link="结果成立后需要说明其适用边界。",
                time_seconds=75,
                visual_strategy="native_chart",
                component_requirements={"text": 1, "chart": 1},
            )

            plan = PagePlanner().build("毕业答辩", ["实验与结果"], [draft], graph)
            json_path, markdown_path = plan.write(root / "audit")

            page = plan.pages[0]
            self.assertEqual(page.evidence_ids, (evidence.evidence_id,))
            self.assertEqual(page.contract.claim_id, claim.claim_id)
            self.assertEqual(page.contract.component_requirements, {"text": 1, "chart": 1})
            self.assertIn("实验结果是否支持模型有效性？", markdown_path.read_text(encoding="utf-8"))
            self.assertTrue(json_path.is_file())
            self.assertTrue(markdown_path.is_file())

    def test_persists_and_reloads_a_validated_complete_scene_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "progress.md"
            source_path.write_text("本周完成实验并记录结果。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(source_path)])
            evidence = graph.all()[0]
            pages = []
            sections = ("本周任务", "文献与学习", "实验与结果", "问题与讨论", "下周计划")
            for index in range(8):
                claim = graph.add_claim(f"进展证据 {index + 1}", [evidence.evidence_id])
                pages.append(PageDraft(
                    page_id=f"P{index + 1:03d}",
                    section=sections[index % len(sections)],
                    title=f"进展证据 {index + 1}",
                    question_answered="本周工作形成了什么证据？",
                    claim_id=claim.claim_id,
                    interpretation="该证据用于验证周报场景契约。",
                    next_link="进入下一项进展。",
                    time_seconds=60,
                    visual_strategy="text_only",
                    component_requirements={"text": 1},
                    coverage_tags=(
                        "period_focus", "completed_tasks", "learning_and_reading", "experiment_progress",
                        "evidence", "failed_attempts", "issues", "discussion", "next_actions",
                    ) if index == 0 else (),
                    argument_units=(
                        "what_was_planned", "what_was_done", "what_was_learned", "what_failed_or_blocked",
                        "what_decision_is_needed", "what_happens_next",
                    ) if index == 0 else (),
                ))
            contract = ScenePlanContract(
                deck_scope="complete",
                evidence_state="interim",
                section_variant="weekly_5",
                duration_minutes=8,
            )

            plan = PagePlanner().build(
                "组会-周报进展",
                list(sections),
                pages,
                graph,
                scene_contract=contract,
            )
            json_path, _ = plan.write(root / "audit")
            restored = PagePlan.load(json_path)

            self.assertEqual(restored.deck_scope, "complete")
            self.assertEqual(restored.evidence_state, "interim")
            self.assertEqual(restored.section_variant, "weekly_5")
            self.assertEqual(restored.coverage_tags, contract.coverage_tags or plan.coverage_tags)
            self.assertEqual(restored.pages[0].argument_units[0], "what_was_planned")


if __name__ == "__main__":
    unittest.main()
