from scripts.extract_figures import select_caption


def test_select_caption_prefers_explicit_label_nearest_image_bottom():
    candidates = [
        {
            "text": "Figure 7 (comparative). Table 5 summarizes adjusted p-values",
            "bbox": [70, 80, 520, 120],
            "label_only": False,
        },
        {"text": "TABLE 3", "bbox": [70, 360, 180, 380], "label_only": True},
        {"text": "FIGURE 6", "bbox": [70, 705, 180, 725], "label_only": True},
    ]

    assert select_caption(candidates, [71, 435, 524, 700]) == "FIGURE 6"


def test_select_caption_uses_position_when_no_label_only_candidate_exists():
    candidates = [
        {
            "text": "Figure 5 is discussed in the following section",
            "bbox": [70, 80, 520, 110],
            "label_only": False,
        },
        {
            "text": "Figure 4. Evaluation workflow and source evidence",
            "bbox": [70, 410, 520, 440],
            "label_only": False,
        },
    ]

    assert select_caption(candidates, [70, 120, 520, 400]).startswith("Figure 4.")
