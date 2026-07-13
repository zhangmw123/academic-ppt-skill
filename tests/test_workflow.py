import json
import tempfile
import unittest
from pathlib import Path

from academic_ppt.workflow import ApprovalKind, ProjectWorkflow, WorkflowConfig


class ProjectWorkflowTests(unittest.TestCase):
    def test_user_can_confirm_a_validated_phase_and_resume_next_phase(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow = ProjectWorkflow.create(
                root,
                WorkflowConfig(
                    scene="毕业答辩",
                    interaction_mode="guided",
                    rigor_profile="standard",
                    authoritative_runtime="powerpoint",
                ),
            )
            brief = root / "audit" / "config.json"
            brief.write_text(json.dumps({"scene": "毕业答辩"}), encoding="utf-8")

            workflow.complete_phase("brief", [brief])
            workflow.approve_phase("brief", ApprovalKind.USER, "素材、场景与模板已确认")
            workflow.begin_phase("evidence")

            resumed = ProjectWorkflow.open(root)
            self.assertEqual(resumed.phase("brief").status, "confirmed")
            self.assertEqual(resumed.phase("evidence").status, "draft")
            self.assertEqual(resumed.phase("brief").confirmation_note, "素材、场景与模板已确认")
            self.assertEqual(resumed.phase("brief").outputs[0].path, "audit/config.json")
            self.assertTrue(resumed.phase("brief").outputs[0].sha256)

    def test_changed_confirmed_artifact_invalidates_that_phase_and_downstream(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow = ProjectWorkflow.create(root, WorkflowConfig(scene="中期考核"))
            for phase_name in ("brief", "evidence", "content_plan"):
                artifact = root / "audit" / f"{phase_name}.json"
                artifact.write_text(json.dumps({"phase": phase_name}), encoding="utf-8")
                if phase_name != "brief":
                    workflow.begin_phase(phase_name)
                workflow.complete_phase(phase_name, [artifact])
                workflow.approve_phase(phase_name, ApprovalKind.USER, f"confirmed {phase_name}")

            (root / "audit" / "evidence.json").write_text("changed", encoding="utf-8")
            changed = workflow.refresh_artifacts()

            self.assertEqual(changed, ["evidence"])
            self.assertEqual(workflow.phase("brief").status, "confirmed")
            self.assertEqual(workflow.phase("evidence").status, "stale")
            self.assertEqual(workflow.phase("content_plan").status, "stale")


if __name__ == "__main__":
    unittest.main()
