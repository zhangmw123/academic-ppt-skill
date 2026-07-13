import tempfile
import unittest
from pathlib import Path

from docx import Document

from academic_ppt.evidence import EvidenceGraph
from academic_ppt.ingest import SourceIngestor
from academic_ppt.planning import PageDraft, PagePlanner
from academic_ppt.speaker import SpeakerScriptWriter


class SpeakerScriptWriterTests(unittest.TestCase):
    def test_writes_editable_docx_script_from_confirmed_page_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "结果.md"
            source_path.write_text("模型 F1 为 92.9%。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(source_path)])
            evidence = graph.all()[0]
            claim = graph.add_claim("模型在测试中达到 92.9 F1。", [evidence.evidence_id])
            plan = PagePlanner().build(
                "毕业答辩",
                ["实验与结果"],
                [PageDraft(
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
                )],
                graph,
            )

            output = SpeakerScriptWriter().write(plan, root / "speaker_script.docx")

            document = Document(output)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            self.assertEqual(output.suffix, ".docx")
            self.assertIn("模型在测试中达到 92.9 F1", text)
            self.assertIn("75 秒", text)
            self.assertIn("结果成立后需要说明其适用边界。", text)


if __name__ == "__main__":
    unittest.main()
