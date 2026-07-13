import tempfile
import unittest
from pathlib import Path

from academic_ppt.evidence import EvidenceGraph
from academic_ppt.ingest import SourceIngestor


class EvidenceGraphTests(unittest.TestCase):
    def test_builds_traceable_result_and_limitation_evidence_from_a_normalized_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "实验结果.md"
            path.write_text(
                "# 实验结果\n模型 F1 为 92.9%。\n边界：仅一个数据集。\n",
                encoding="utf-8",
            )
            source = SourceIngestor().ingest(path)

            graph = EvidenceGraph.from_sources([source])
            evidence = graph.for_source(source.source_id)

            self.assertEqual([item.evidence_type for item in evidence], ["context", "result", "limitation"])
            self.assertEqual(evidence[1].text, "模型 F1 为 92.9%。")
            self.assertEqual(evidence[1].locator, {"line": 2})
            self.assertEqual(evidence[1].source_id, source.source_id)
            self.assertEqual(evidence[1].source_block_id, "B0002")
            self.assertTrue(evidence[1].evidence_id.startswith("EVD_"))

    def test_classifies_conflicting_reported_metric_values_as_material_with_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_path = root / "论文结果.md"
            first_path.write_text("模型 F1 为 92.9%。", encoding="utf-8")
            second_path = root / "增量结果.md"
            second_path.write_text("模型 F1 为 90.1%。", encoding="utf-8")
            first = SourceIngestor().ingest(first_path, role="primary_evidence")
            second = SourceIngestor().ingest(second_path, role="incremental_evidence")

            conflicts = EvidenceGraph.from_sources([first, second]).conflicts()

            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0].severity, "material")
            self.assertEqual(conflicts[0].metric, "f1")
            self.assertEqual(conflicts[0].values, (90.1, 92.9))
            self.assertEqual(set(conflicts[0].evidence_ids), {
                "EVD_" + first.source_id.removeprefix("SRC_") + "_B0001",
                "EVD_" + second.source_id.removeprefix("SRC_") + "_B0001",
            })

    def test_claim_must_bind_existing_evidence_and_can_be_traced_back_to_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "结论.md"
            path.write_text("模型 F1 为 92.9%。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(path)])
            evidence = graph.all()[0]

            claim = graph.add_claim("模型在测试中达到 92.9 F1。", [evidence.evidence_id])

            self.assertTrue(claim.claim_id.startswith("CLM_"))
            self.assertEqual(claim.evidence_ids, (evidence.evidence_id,))
            self.assertEqual(graph.trace_claim(claim.claim_id), (evidence,))
            with self.assertRaisesRegex(ValueError, "unknown evidence"):
                graph.add_claim("无来源结论", ["EVD_MISSING"])

    def test_visual_task_traces_from_a_planned_page_back_to_its_source_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "结果.md"
            path.write_text("模型 F1 为 92.9%。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(path)])
            evidence = graph.all()[0]
            claim = graph.add_claim("模型达到 92.9 F1。", [evidence.evidence_id])

            page = graph.add_page("P001", [claim.claim_id])
            visual = graph.add_visual_task("VIS_001", page.page_id, [evidence.evidence_id])

            self.assertEqual(page.claim_ids, (claim.claim_id,))
            self.assertEqual(visual.page_id, "P001")
            self.assertEqual(visual.evidence_ids, (evidence.evidence_id,))
            self.assertEqual(graph.trace_page("P001"), (claim,))
            self.assertEqual(graph.trace_visual("VIS_001"), (evidence,))
            with self.assertRaisesRegex(ValueError, "not bound to page claims"):
                graph.add_visual_task("VIS_002", "P001", ["EVD_MISSING"])

    def test_authorized_derived_value_conflicting_with_reported_metric_is_blocking(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "报告结果.md"
            path.write_text("模型 F1 为 92.9%。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(path)])
            reported = graph.all()[0]

            derived = graph.add_derived_evidence(
                "系统计算 F1 为 90.1%。",
                [reported.evidence_id],
                metric="f1",
                value=90.1,
                authorization_note="用户已授权复算 F1。",
            )

            conflict = graph.conflicts()[0]
            self.assertEqual(derived.evidence_type, "derived_analysis")
            self.assertEqual(conflict.severity, "blocking")
            self.assertEqual(conflict.values, (90.1, 92.9))
            self.assertEqual(set(conflict.evidence_ids), {reported.evidence_id, derived.evidence_id})


if __name__ == "__main__":
    unittest.main()
