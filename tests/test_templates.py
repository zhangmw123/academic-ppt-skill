import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches

from academic_ppt.layout import LayoutCompiler, ScientificPageContract
from academic_ppt.templates import TemplateCapabilityGraph


class TemplateCapabilityGraphTests(unittest.TestCase):
    def test_selects_a_native_slide_with_required_editable_component_capacity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "figure.png"
            Image.new("RGB", (320, 180), "white").save(image_path)
            template_path = root / "template.pptx"
            presentation = Presentation()
            text_only = presentation.slides.add_slide(presentation.slide_layouts[6])
            text_only.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = "标题"
            figure_page = presentation.slides.add_slide(presentation.slide_layouts[6])
            figure_page.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = "图表标题"
            figure_page.shapes.add_picture(str(image_path), Inches(1), Inches(2), Inches(4), Inches(2))
            presentation.save(template_path)

            graph = TemplateCapabilityGraph.from_presentation(template_path)
            candidates = graph.find_compatible_slides({"text": 1, "picture": 1})

            self.assertEqual(graph.slides[1].slide_index, 2)
            self.assertEqual(candidates, (graph.slides[1],))
            self.assertEqual(graph.slides[1].component_counts, {"picture": 1, "text": 1})

    def test_layout_compiler_uses_compatible_native_template_slide_for_page_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "figure.png"
            Image.new("RGB", (320, 180), "white").save(image_path)
            template_path = root / "template.pptx"
            presentation = Presentation()
            text_only = presentation.slides.add_slide(presentation.slide_layouts[6])
            text_only.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = "标题"
            figure_page = presentation.slides.add_slide(presentation.slide_layouts[6])
            figure_page.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = "图表标题"
            figure_page.shapes.add_picture(str(image_path), Inches(1), Inches(2), Inches(4), Inches(2))
            presentation.save(template_path)
            graph = TemplateCapabilityGraph.from_presentation(template_path)
            contract = ScientificPageContract(
                page_id="P001",
                claim_id="CLM_001",
                component_requirements={"text": 1, "picture": 1},
            )

            decision = LayoutCompiler(graph).compile(contract)

            self.assertEqual(decision.render_mode, "template_native")
            self.assertEqual(decision.source_slide_index, 2)
            self.assertIsNone(decision.fallback_reason)

    def test_layout_decision_binds_required_content_to_original_template_shape_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "figure.png"
            Image.new("RGB", (320, 180), "white").save(image_path)
            template_path = root / "template.pptx"
            presentation = Presentation()
            slide = presentation.slides.add_slide(presentation.slide_layouts[6])
            slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = "标题"
            slide.shapes.add_picture(str(image_path), Inches(1), Inches(2), Inches(4), Inches(2))
            presentation.save(template_path)
            graph = TemplateCapabilityGraph.from_presentation(template_path)
            contract = ScientificPageContract(
                page_id="P001",
                claim_id="CLM_001",
                component_requirements={"text": 1, "picture": 1},
            )

            decision = LayoutCompiler(graph).compile(contract)

            expected = {
                kind: tuple(component.shape_id for component in graph.slides[0].components if component.kind == kind)
                for kind in ("text", "picture")
            }
            self.assertEqual(decision.component_bindings, expected)


if __name__ == "__main__":
    unittest.main()
