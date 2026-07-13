import tempfile
import unittest
from pathlib import Path

from PIL import Image

from academic_ppt.service import AcademicPptService
from academic_ppt.service import ContentPageDraft
from academic_ppt.scenes import ScenePlanContract
from academic_ppt.workflow import ProjectWorkflow


class AcademicPptServiceTests(unittest.TestCase):
    def test_prepare_resolves_a_scene_alias_before_creating_the_workflow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "proposal.md"
            source.write_text("模型 算法 初步实验 技术路线。", encoding="utf-8")

            summary = AcademicPptService().prepare(root, [source], scene="开题")

            self.assertEqual(summary["scene"], "开题答辩")
            self.assertEqual(ProjectWorkflow.open(root).config.scene, "开题答辩")
            self.assertEqual(summary["scene_contract"]["complete_min"], 12)

    def test_prepare_creates_confirmable_guided_task_summary_from_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "model.md"
            source.write_text("模型 算法 训练 数据集 基线 消融 泛化。\n模型 F1 为 92.9%。", encoding="utf-8")

            summary = AcademicPptService().prepare(root, [source], scene="毕业答辩")

            workflow = ProjectWorkflow.open(root)
            self.assertEqual(summary["scene"], "毕业答辩")
            self.assertEqual(summary["method_profiles"]["primary"], "computational_modeling")
            self.assertEqual(summary["template"]["id"], "T02")
            self.assertTrue((root / "audit" / "task_summary.json").is_file())
            self.assertEqual(workflow.phase("brief").status, "awaiting_confirmation")

            AcademicPptService().confirm_brief(root, "任务摘要已确认")

            self.assertEqual(ProjectWorkflow.open(root).phase("evidence").status, "draft")

    def test_prepares_evidence_and_storyline_options_after_the_brief_is_confirmed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "model.md"
            source.write_text("Model method.\nModel F1 reached 92.9%.\nBoundary: one dataset.", encoding="utf-8")
            service = AcademicPptService()
            service.prepare(root, [source], scene="毕业答辩")
            service.confirm_brief(root, "Confirmed")

            evidence = service.prepare_evidence(root)

            workflow = ProjectWorkflow.open(root)
            self.assertEqual(len(evidence["options"]), 3)
            self.assertEqual(evidence["recommended"]["option_id"], "problem_method_evidence")
            self.assertEqual(workflow.phase("evidence").status, "awaiting_confirmation")
            self.assertTrue((root / "audit" / "storyline_options.json").is_file())

    def test_prepares_an_evidence_bound_content_plan_after_evidence_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "model.md"
            source.write_text("Model F1 reached 92.9%.", encoding="utf-8")
            service = AcademicPptService()
            service.prepare(root, [source], scene="毕业答辩")
            service.confirm_brief(root, "Confirmed")
            service.prepare_evidence(root)
            service.confirm_evidence(root, "Confirmed evidence and storyline")
            payload = __import__("json").loads((root / "audit" / "evidence_summary.json").read_text(encoding="utf-8"))

            plan = service.prepare_content_plan(root, ["Results"], [ContentPageDraft(
                page_id="P001", section="Results", title="Model F1 reached 92.9%.",
                question_answered="Does the result support the model?",
                claim_text="Model F1 reached 92.9%.", evidence_ids=(payload["evidence"][0]["evidence_id"],),
                interpretation="The reported result supports effectiveness within one dataset.",
                next_link="Discuss the boundary.", time_seconds=60, visual_strategy="native_chart",
                component_requirements={"text": 1, "picture": 1},
            )])

            self.assertEqual(plan.pages[0].page_id, "P001")
            self.assertEqual(ProjectWorkflow.open(root).phase("content_plan").status, "awaiting_confirmation")
            self.assertTrue((root / "audit" / "page_plan.json").is_file())

    def test_prepares_template_layout_and_visual_tasks_after_content_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "model.md"
            source.write_text("Model F1 reached 92.9%.", encoding="utf-8")
            service = AcademicPptService()
            service.prepare(root, [source], scene="毕业答辩")
            service.confirm_brief(root, "Confirmed")
            service.prepare_evidence(root)
            service.confirm_evidence(root, "Confirmed evidence")
            evidence = __import__("json").loads((root / "audit" / "evidence_summary.json").read_text(encoding="utf-8"))
            service.prepare_content_plan(root, ["Results"], [ContentPageDraft(
                page_id="P001", section="Results", title="Model F1 reached 92.9%.",
                question_answered="Does the result support the model?", claim_text="Model F1 reached 92.9%.",
                evidence_ids=(evidence["evidence"][0]["evidence_id"],),
                interpretation="The result is limited to one dataset.", next_link="Discuss the boundary.",
                time_seconds=60, visual_strategy="source_figure", component_requirements={"text": 1, "picture": 1},
            )])
            service.confirm_content_plan(root, "Confirmed page plan")

            visual = service.prepare_visual_plan(root)

            self.assertEqual(visual["layout_decisions"]["P001"]["render_mode"], "template_native")
            self.assertEqual(visual["visual_tasks"][0]["page_id"], "P001")
            self.assertEqual(ProjectWorkflow.open(root).phase("visual_plan").status, "awaiting_confirmation")

    def test_renders_a_confirmed_visual_plan_into_a_reviewable_sample(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "model.md"
            image = Path(temp_dir) / "result.png"
            source.write_text("Model F1 reached 92.9%.", encoding="utf-8")
            Image.new("RGB", (240, 160), "blue").save(image)
            service = AcademicPptService()
            service.prepare(root, [source], scene="毕业答辩")
            service.confirm_brief(root, "Confirmed")
            service.prepare_evidence(root)
            service.confirm_evidence(root, "Confirmed evidence")
            evidence = __import__("json").loads((root / "audit" / "evidence_summary.json").read_text(encoding="utf-8"))
            service.prepare_content_plan(root, ["Results"], [ContentPageDraft(
                page_id="P001", section="Results", title="Model F1 reached 92.9%.",
                question_answered="Does the result support the model?", claim_text="Model F1 reached 92.9%.",
                evidence_ids=(evidence["evidence"][0]["evidence_id"],),
                interpretation="The result is limited to one dataset.", next_link="Discuss the boundary.",
                time_seconds=60, visual_strategy="source_figure", component_requirements={"text": 1, "picture": 1},
            )])
            service.confirm_content_plan(root, "Confirmed page plan")
            service.prepare_visual_plan(root)
            service.confirm_visual_plan(root, "Confirmed visual blueprint")

            sample = service.render_sample(root, {"P001": ["Model F1 reached 92.9%."]}, {"P001": [image]})

            self.assertTrue(Path(sample["pptx"]).is_file())
            self.assertTrue(Path(sample["report"]).is_file())
            self.assertEqual(ProjectWorkflow.open(root).phase("sample").status, "awaiting_confirmation")

    def test_publishes_a_confirmed_sample_as_a_nonformal_delivery_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            source = Path(temp_dir) / "model.md"
            image = Path(temp_dir) / "result.png"
            source.write_text("Model F1 reached 92.9%.", encoding="utf-8")
            Image.new("RGB", (240, 160), "blue").save(image)
            service = AcademicPptService()
            service.prepare(root, [source], scene="毕业答辩")
            service.confirm_brief(root, "Confirmed")
            service.prepare_evidence(root)
            service.confirm_evidence(root, "Confirmed evidence")
            evidence = __import__("json").loads((root / "audit" / "evidence_summary.json").read_text(encoding="utf-8"))
            service.prepare_content_plan(root, ["Results"], [ContentPageDraft(
                page_id="P001", section="Results", title="Model F1 reached 92.9%.",
                question_answered="Does the result support the model?", claim_text="Model F1 reached 92.9%.",
                evidence_ids=(evidence["evidence"][0]["evidence_id"],),
                interpretation="The result is limited to one dataset.", next_link="Discuss the boundary.",
                time_seconds=60, visual_strategy="source_figure", component_requirements={"text": 1, "picture": 1},
            )])
            service.confirm_content_plan(root, "Confirmed page plan")
            service.prepare_visual_plan(root)
            service.confirm_visual_plan(root, "Confirmed visual blueprint")
            service.render_sample(root, {"P001": ["Model F1 reached 92.9%."]}, {"P001": [image]})
            service.confirm_sample(root, "Confirmed representative render")

            delivery = service.publish_delivery(root)

            self.assertEqual({Path(path).suffix for path in delivery["visible_files"]}, {".pptx", ".docx"})
            self.assertFalse(delivery["formal_accepted"])
            self.assertEqual(ProjectWorkflow.open(root).phase("delivery").status, "awaiting_confirmation")


if __name__ == "__main__":
    unittest.main()
