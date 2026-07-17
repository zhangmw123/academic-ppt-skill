"""Compile real source evidence into a complete scene-aware page payload."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .evidence import EvidenceNode
from .scenes import SceneCatalog, ScenePlanContract


@dataclass(frozen=True)
class CompleteContentDraft:
    page_id: str
    section: str
    title: str
    question_answered: str
    claim_text: str
    evidence_ids: tuple[str, ...]
    interpretation: str
    next_link: str
    time_seconds: int
    visual_strategy: str
    component_requirements: dict[str, int]
    coverage_tags: tuple[str, ...] = ()
    argument_units: tuple[str, ...] = ()
    media_scope: str = "none"
    media_layout: str = "none"


SPACE = re.compile(r"\s+")
SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？!?])\s+|(?<=\.)\s+(?=[A-Z\u4e00-\u9fff])")
REFERENCE = re.compile(r"^\s*(references|参考文献|\[\d+\]|\d+\.\s*[A-Z][a-z]+,)", re.I)
CAPTION_OR_TABULAR = re.compile(r"^\s*(?:figure|table)\s+\d+\b", re.I)
BOILERPLATE = ("reviewed by", "copyright", "conflict of interest", "publisher's note", "frontiers in")
PARENTHETICAL_CITATION = re.compile(r"^\([^)]{2,120}(?:19|20)\d{2}[a-z]?\)\.?\s*", re.I)
TRAILING_CONNECTORS = {
    "a", "according", "an", "and", "as", "by", "each", "for", "in", "of", "on", "or", "that", "the", "to", "while", "with",
}
EVIDENCE_CLAIM_LIMIT = 128
EVIDENCE_LINE_LIMIT = 64

ROLE_LABELS = {
    "cover": "汇报主题",
    "ending": "结论",
    "paper_metadata": "论文定位",
    "venue_context": "发表信息",
    "author_context": "作者与机构",
    "research_background": "研究背景",
    "research_problem": "核心问题",
    "related_work": "相关研究",
    "research_gap": "现有缺口",
    "objectives": "研究目标",
    "method": "核心方法",
    "methods": "技术路线",
    "data": "数据与知识来源",
    "experiments": "实验设计",
    "results": "关键结果",
    "innovation": "方法创新",
    "contributions": "研究贡献",
    "limitations": "局限与边界",
    "future_work": "后续工作",
    "research_inspiration": "可迁移启发",
    "next_action": "验证行动",
}

ROLE_KEYWORDS = {
    "cover": ("title", "abstract", "crop graphrag", "题目", "摘要", "云南植物"),
    "ending": ("conclusion", "future", "contribution", "结论", "总结", "展望", "贡献"),
    "paper_metadata": ("title", "abstract", "crop graphrag", "题目", "摘要"),
    "venue_context": ("doi", "journal", "published", "frontiers", "发表", "学位"),
    "author_context": ("author", "institute", "university", "作者", "学院", "指导教师"),
    "research_background": ("background", "importance", "security", "resource", "yunnan plant", "背景", "意义", "现状", "资源", "云南", "植物"),
    "research_problem": ("problem", "challenge", "however", "lack", "问题", "困难", "不足", "缺乏"),
    "related_work": ("existing", "previous", "researchers", "related", "国内", "国外", "已有", "研究现状"),
    "research_gap": ("limitation", "gap", "insufficient", "however", "不足", "缺口", "局限", "尚未"),
    "objectives": ("objective", "aim", "in order to", "目标", "目的", "本文"),
    "method": ("framework", "method", "workflow", "model", "graph", "方法", "模型", "流程", "框架"),
    "methods": ("framework", "method", "architecture", "bert", "bilstm", "globalpointer", "neo4j", "方法", "模型", "架构", "知识图谱"),
    "data": ("dataset", "corpus", "records", "data source", "数据", "语料", "样本", "三元组"),
    "experiments": ("experiment", "baseline", "ablation", "evaluation", "实验", "对比", "消融", "测试"),
    "results": ("result", "accuracy", "recall", "precision", "f1", "结果", "准确率", "召回率", "提升"),
    "innovation": ("novel", "propose", "innovation", "new framework", "创新", "提出", "首次"),
    "contributions": (
        "contribution", "utility", "effective", "constructed", "designed", "implemented", "validated",
        "贡献", "实现", "构建", "完成",
    ),
    "limitations": ("limitation", "boundary", "constraint", "failure", "cannot", "局限", "不足", "失败", "无法", "超出"),
    "future_work": ("future", "next", "further", "未来", "后续", "进一步", "展望"),
    "research_inspiration": ("mechanism", "transfer", "framework", "机制", "迁移", "启发", "框架"),
    "next_action": ("ablation", "replication", "metric", "evaluate", "复现", "消融", "指标", "验证"),
}

ROLE_RANGES = {
    "cover": (0.0, 0.12), "ending": (0.65, 0.92),
    "paper_metadata": (0.0, 0.12), "venue_context": (0.0, 0.15), "author_context": (0.0, 0.15),
    "research_background": (0.02, 0.3), "research_problem": (0.02, 0.4), "related_work": (0.08, 0.45),
    "research_gap": (0.08, 0.5), "objectives": (0.02, 0.35), "method": (0.15, 0.68),
    "methods": (0.15, 0.7), "data": (0.15, 0.65), "experiments": (0.48, 0.82),
    "results": (0.55, 0.86), "innovation": (0.45, 0.9), "contributions": (0.58, 0.9),
    "limitations": (0.65, 0.92), "future_work": (0.68, 0.92), "research_inspiration": (0.3, 0.88),
    "next_action": (0.45, 0.9),
}

ROLE_ALIASES = {
    "motivation": "research_background",
    "problem": "research_problem",
    "experiment_setup": "experiments",
    "key_results": "results",
    "contribution": "contributions",
    "takeaway": "ending",
}

SCENE_FOCUS = {
    "组会-文献精读": (
        "cover", "paper_metadata", "research_problem", "research_gap", "method",
        "experiments", "results", "limitations", "research_inspiration", "ending",
    ),
    "毕业答辩": (
        "cover", "research_background", "research_problem", "related_work", "research_gap", "objectives",
        "methods", "methods", "data", "methods", "experiments", "experiments", "results",
        "results", "innovation", "contributions", "limitations", "ending",
    ),
}


@dataclass(frozen=True)
class CompleteContentPackage:
    sections: tuple[str, ...]
    drafts: tuple[CompleteContentDraft, ...]
    scene_contract: ScenePlanContract
    text_content: dict[str, list[str]]
    image_content: dict[str, list[str]]
    figure_manifests: tuple[str, ...]


@dataclass(frozen=True)
class EvidencePassage:
    nodes: tuple[EvidenceNode, ...]
    text: str
    page: int | None

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(node.evidence_id for node in self.nodes)

    @property
    def locator(self) -> dict:
        return dict(self.nodes[0].locator)


class CompleteContentCompiler:
    """Create one distinct evidence-bound argument for every final slide."""

    def compile(
        self,
        *,
        scene: str,
        evidence: list[EvidenceNode],
        source_paths: list[Path],
        working_dir: Path,
        target_pages: int | None = None,
    ) -> CompleteContentPackage:
        profile = SceneCatalog.load().resolve(scene)
        page_count = target_pages or profile.complete_min
        if not profile.complete_min <= page_count <= profile.complete_max:
            raise ValueError(
                f"target page count {page_count} is outside {profile.complete_min}-{profile.complete_max} for {profile.name}"
            )
        candidates = self._evidence_passages(evidence)
        if len(candidates) < page_count:
            raise ValueError(
                f"complete deck requires {page_count} distinct textual evidence blocks; found {len(candidates)}"
            )
        variant_name, sections = next(iter(profile.default_variants.items()))
        focus_sequence = self._focus_sequence(profile.name, page_count, profile.required_tags)
        selected = self._select_for_focus(candidates, focus_sequence)
        figures, manifests = self._extract_figures(source_paths, working_dir / "figures")
        figure_pool = list(figures)
        tags_by_page = self._distribute(profile.required_tags, page_count)
        arguments_by_page = self._distribute(profile.argument_chain, page_count)
        total_seconds = page_count * 60
        base, remainder = divmod(total_seconds, page_count)
        drafts = []
        text_content: dict[str, list[str]] = {}
        image_content: dict[str, list[str]] = {}
        cover_title = self._cover_title(source_paths, evidence)

        for index, (focus, primary) in enumerate(zip(focus_sequence, selected)):
            page_id = f"P{index + 1:03d}"
            section = sections[min(index * len(sections) // page_count, len(sections) - 1)]
            title = cover_title if index == 0 else self._title(primary.text, focus, index, page_count)
            claim = self._claim(primary.text, focus)
            evidence_line = self._evidence_line(primary, focus)
            draft_transition = (
                "由此进入总结与行动。"
                if index == page_count - 1
                else f"下一页转向{sections[min((index + 1) * len(sections) // page_count, len(sections) - 1)]}。"
            )
            image = self._page_figure(
                figure_pool,
                primary.page,
                index,
                page_count,
                focus=focus,
                claim=claim,
            )
            if index in {0, page_count - 1}:
                interpretation = self._interpretation(primary, index, page_count, focus=focus)
                visual_strategy = "text_only"
                components = {"text": 2}
                media_scope = "none"
                media_layout = "none"
                page_text = [
                    title,
                    self._cover_subtitle(scene, source_paths) if index == 0 else "核心结论与可验证的后续行动",
                ]
            elif image is not None:
                interpretation = self._interpretation(primary, index, page_count, focus=focus)
                visual_strategy = "source_figure"
                components = {"text": 3, "picture": 1}
                media_scope = "page"
                media_layout = "one_image"
                image_content[page_id] = [image["path"]]
                page_text = [title, claim, interpretation]
            else:
                visual_strategy = self._native_strategy(focus, index, page_count)
                interpretation = self._interpretation(
                    primary,
                    index,
                    page_count,
                    focus=focus,
                    skip_evidence_excerpt=visual_strategy != "native_diagram",
                )
                media_scope = "none"
                media_layout = "none"
                if visual_strategy == "native_diagram":
                    components = {"text": 6}
                    page_text = [
                        title,
                        *self._process_steps(primary.text, focus, claim, interpretation, draft_transition),
                    ]
                else:
                    components = {"text": 4}
                    page_text = [title, claim, evidence_line, interpretation]
            draft = CompleteContentDraft(
                page_id=page_id,
                section=section,
                title=title,
                question_answered=f"{section}中的哪项证据决定当前判断？",
                claim_text=claim,
                evidence_ids=self._supporting_evidence(primary, candidates),
                interpretation=interpretation,
                next_link=draft_transition,
                time_seconds=base + (1 if index < remainder else 0),
                visual_strategy=visual_strategy,
                component_requirements=components,
                coverage_tags=tags_by_page[index],
                argument_units=arguments_by_page[index],
                media_scope=media_scope,
                media_layout=media_layout,
            )
            drafts.append(draft)
            text_content[page_id] = page_text

        evidence_state = self._evidence_state(profile.name, profile.evidence_states)
        contract = ScenePlanContract(
            deck_scope="complete",
            evidence_state=evidence_state,
            section_variant=variant_name,
            duration_minutes=total_seconds / 60,
        )
        return CompleteContentPackage(
            sections=tuple(sections),
            drafts=tuple(drafts),
            scene_contract=contract,
            text_content=text_content,
            image_content=image_content,
            figure_manifests=tuple(str(path) for path in manifests),
        )

    @staticmethod
    def _evidence_passages(evidence: list[EvidenceNode]) -> list[EvidencePassage]:
        text_frequency: dict[str, int] = {}
        for node in evidence:
            key = SPACE.sub(" ", node.text).strip().casefold()
            if key:
                text_frequency[key] = text_frequency.get(key, 0) + 1
        by_page: dict[tuple[str, int | None], list[EvidenceNode]] = {}
        for node in evidence:
            if node.evidence_type == "asset" or not node.text.strip():
                continue
            page = node.locator.get("page")
            by_page.setdefault((node.source_id, int(page) if page is not None else None), []).append(node)
        passages = []
        for (_, page), nodes in by_page.items():
            nodes.sort(key=lambda node: int(node.locator.get("block", node.locator.get("line", 0))))
            current: list[EvidenceNode] = []
            text_parts: list[str] = []
            for node in nodes:
                value = SPACE.sub(" ", node.text).strip()
                if not value:
                    continue
                if text_frequency.get(value.casefold(), 0) >= 3 and len(value) < 100:
                    continue
                if current and sum(len(part) for part in text_parts) + len(value) > 650:
                    passages.append(EvidencePassage(tuple(current), " ".join(text_parts), page))
                    current, text_parts = [], []
                current.append(node)
                text_parts.append(value)
                if sum(len(part) for part in text_parts) >= 260 or len(current) >= 4:
                    passages.append(EvidencePassage(tuple(current), " ".join(text_parts), page))
                    current, text_parts = [], []
            if current:
                passages.append(EvidencePassage(tuple(current), " ".join(text_parts), page))
        return [passage for passage in passages if CompleteContentCompiler._passage_is_usable(passage)]

    @staticmethod
    def _passage_is_usable(passage: EvidencePassage) -> bool:
        text = passage.text.strip()
        lowered = text.casefold()
        meaningful = sum(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in text)
        if len(text) < 70 or meaningful < 55 or REFERENCE.match(text) or CAPTION_OR_TABULAR.match(text):
            return False
        if CompleteContentCompiler._bibliography_prefix_end(text) is not None:
            return False
        if any(marker in lowered for marker in BOILERPLATE):
            return False
        if len(re.findall(r"\[\d+\]", text)) >= 3:
            return False
        return True

    @staticmethod
    def _select_for_focus(passages: list[EvidencePassage], focuses: tuple[str, ...]) -> list[EvidencePassage]:
        max_page = max((passage.page or 1 for passage in passages), default=1)
        cjk_preferred = sum(sum("\u4e00" <= char <= "\u9fff" for char in p.text) for p in passages) > sum(len(p.text) for p in passages) * 0.15
        selected = []
        used = set()
        for focus in focuses:
            candidates = [(CompleteContentCompiler._focus_score(p, focus, max_page, cjk_preferred), index, p)
                          for index, p in enumerate(passages) if index not in used]
            if not candidates:
                raise ValueError("not enough distinct evidence passages for the complete focus sequence")
            _, index, passage = max(candidates, key=lambda item: (item[0], -item[1]))
            used.add(index)
            selected.append(passage)
        return selected

    @staticmethod
    def _focus_score(passage: EvidencePassage, focus: str, max_page: int, cjk_preferred: bool) -> float:
        focus = CompleteContentCompiler._canonical_role(focus)
        lowered = passage.text.casefold()
        keyword_score = sum(1 for keyword in ROLE_KEYWORDS.get(focus, ()) if keyword.casefold() in lowered) * 12
        start, end = ROLE_RANGES.get(focus, (0.0, 1.0))
        position = (passage.page or 1) / max(max_page, 1)
        range_score = 12 if start <= position <= end else -25 * min(abs(position - start), abs(position - end))
        cjk_ratio = sum("\u4e00" <= char <= "\u9fff" for char in passage.text) / max(len(passage.text), 1)
        language_score = cjk_ratio * 10 if cjk_preferred else (1 - cjk_ratio) * 4
        type_score = sum(node.evidence_type in {"method", "result", "limitation"} for node in passage.nodes) * 2
        role_score = 0
        if focus == "results":
            role_score += sum(node.evidence_type == "result" for node in passage.nodes) * 6
            role_score += min(len(re.findall(r"\b\d+(?:\.\d+)?%", passage.text)), 4) * 4
        elif focus == "contributions":
            role_score += sum(node.evidence_type == "result" for node in passage.nodes) * 6
            role_score += sum(
                marker in lowered
                for marker in ("we constructed", "we designed", "we implemented", "we validated", "this study proposes")
            ) * 10
        elif focus == "limitations":
            role_score += sum(node.evidence_type == "limitation" for node in passage.nodes) * 30
        return keyword_score + range_score + language_score + type_score + role_score + min(len(passage.text), 500) / 100

    @staticmethod
    def _focus_sequence(scene: str, page_count: int, required_tags: tuple[str, ...]) -> tuple[str, ...]:
        base = SCENE_FOCUS.get(scene, required_tags)
        if len(base) == page_count:
            return tuple(base)
        return tuple(base[min(index * len(base) // page_count, len(base) - 1)] for index in range(page_count))

    @staticmethod
    def _distribute(values: tuple[str, ...], page_count: int) -> list[tuple[str, ...]]:
        return [tuple(value for index, value in enumerate(values) if index % page_count == page) for page in range(page_count)]

    @staticmethod
    def _title(text: str, focus: str, index: int, page_count: int) -> str:
        focus = CompleteContentCompiler._canonical_role(focus)
        cleaned = CompleteContentCompiler._role_excerpt(text, focus)
        sentence = CompleteContentCompiler._sentences(cleaned)[0]
        sentence = re.sub(r"^(?:taken together|overall),\s*", "", sentence, flags=re.I)
        reporting = re.search(
            r"\b(?:shows?|demonstrates?|indicates?|confirms?)\s+that\s+",
            sentence,
            flags=re.I,
        )
        if reporting is not None and reporting.start() < 80:
            sentence = sentence[reporting.end():]
        if sentence.casefold().startswith("for both ") and "," in sentence:
            sentence = sentence.split(",", 1)[0]
        if re.match(r"^(?:after|although|because|before|by|given|using|when|while)\b", sentence, flags=re.I):
            _, separator, main_clause = sentence.partition(",")
            if separator and len(main_clause.strip()) >= 20:
                sentence = main_clause.strip()
        sentence = re.split(
            r"\s+and\s+(?=(?:apply|conduct|construct|derive|employ|enable|evaluate|generate|perform|provide|use)\b)",
            sentence,
            maxsplit=1,
            flags=re.I,
        )[0]
        sentence = re.split(r",\s+(?:with|while|whereas|which|including)\b", sentence, maxsplit=1, flags=re.I)[0]
        copula = re.match(r"^(.{30,90}?)\s+(?:is|are|was|were)\s+", sentence, flags=re.I)
        if copula is not None and len(sentence) > 72:
            sentence = copula.group(1)
        sentence = sentence.rstrip(" ，,。.;；:：")
        label = ROLE_LABELS.get(focus, "证据判断")
        short = CompleteContentCompiler._clip_text(sentence, 72)
        if short and short[0].isascii() and short[0].islower():
            short = short[0].upper() + short[1:]
        if sum(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in short) < 5:
            short = "证据指向当前判断"
        if index == page_count - 1:
            return f"{label}：证据收束为下一步行动"
        if focus == "cover":
            return CompleteContentCompiler._clip_text(short, 54)
        return CompleteContentCompiler._clip_text(f"{label}：{short}", 88)

    @staticmethod
    def _cover_title(source_paths: list[Path], evidence: list[EvidenceNode]) -> str:
        generic_stems = {"test", "paper", "document", "测试文件"}
        for source in source_paths:
            stem = SPACE.sub(" ", source.stem).strip()
            if stem and stem.casefold() not in generic_stems:
                return CompleteContentCompiler._clip_text(stem, 52)
        first_page = [
            SPACE.sub(" ", node.text).strip()
            for node in evidence
            if node.evidence_type != "asset"
            and int(node.locator.get("page", 0) or 0) == 1
            and 30 <= len(SPACE.sub(" ", node.text).strip()) <= 180
        ]
        if first_page:
            title = first_page[0]
            return CompleteContentCompiler._clip_text(title, 52)
        return CompleteContentCompiler._clip_text(SPACE.sub(" ", source_paths[0].stem).strip(), 52)

    @staticmethod
    def _cover_subtitle(scene: str, source_paths: list[Path]) -> str:
        source_kind = "论文" if any(path.suffix.casefold() == ".pdf" for path in source_paths) else "研究材料"
        return f"{scene} | 基于{source_kind}原文证据生成"

    @staticmethod
    def _claim(text: str, focus: str | None = None) -> str:
        return CompleteContentCompiler._claim_parts(text, focus)[0]

    @staticmethod
    def _claim_parts(text: str, focus: str | None = None) -> tuple[str, str]:
        role_text = CompleteContentCompiler._role_excerpt(text, focus)
        if CompleteContentCompiler._canonical_role(focus) == "limitations":
            sentences = CompleteContentCompiler._sentences(role_text)
            if len(sentences) >= 2:
                raw_pair = " ".join(sentences[:2])
                if len(raw_pair) <= EVIDENCE_CLAIM_LIMIT + 24:
                    tail = role_text[len(raw_pair):].lstrip(" ，,。.;；:：")
                    return raw_pair.rstrip(" ，,。.;；:："), tail
        prefix = role_text[:EVIDENCE_CLAIM_LIMIT + 1]
        has_strong_boundary = bool(re.search(r"[。！？.!?;；:：](?:\s+|$)", prefix))
        if len(role_text) > EVIDENCE_CLAIM_LIMIT and not has_strong_boundary:
            lookahead = role_text[EVIDENCE_CLAIM_LIMIT:EVIDENCE_CLAIM_LIMIT + 33]
            nearby_boundary = re.search(r"[。！？.!?;；:：,，](?:\s+|$)", lookahead)
            if nearby_boundary is not None:
                boundary = EVIDENCE_CLAIM_LIMIT + nearby_boundary.end()
                return (
                    role_text[:boundary].rstrip(" ，,。.;；:："),
                    role_text[boundary:].lstrip(" ，,。.;；:："),
                )
        return CompleteContentCompiler._split_excerpt(role_text, EVIDENCE_CLAIM_LIMIT)

    @staticmethod
    def _evidence_line(primary: EvidencePassage, focus: str | None = None) -> str:
        location = f"第{primary.page}页" if primary.page is not None else json.dumps(primary.locator, ensure_ascii=False)
        first = f"来源：{location}"
        _, remainder = CompleteContentCompiler._claim_parts(primary.text, focus)
        if CompleteContentCompiler._canonical_role(focus) == "limitations":
            second, _ = CompleteContentCompiler._complete_sentence_excerpt(
                remainder,
                EVIDENCE_LINE_LIMIT,
                maximum_extra=40,
            )
        else:
            second = CompleteContentCompiler._clip_text(remainder, EVIDENCE_LINE_LIMIT)
        return f"{first}\n补充证据：{second}"

    @staticmethod
    def _interpretation(
        node: EvidencePassage,
        index: int,
        page_count: int,
        *,
        focus: str | None = None,
        skip_evidence_excerpt: bool = False,
    ) -> str:
        cleaned = CompleteContentCompiler._role_excerpt(node.text, focus)
        _, remainder = CompleteContentCompiler._claim_parts(node.text, focus)
        if skip_evidence_excerpt and remainder:
            if CompleteContentCompiler._canonical_role(focus) == "limitations":
                _, remainder = CompleteContentCompiler._complete_sentence_excerpt(
                    remainder,
                    EVIDENCE_LINE_LIMIT,
                    maximum_extra=40,
                )
            else:
                _, remainder = CompleteContentCompiler._split_excerpt(remainder, EVIDENCE_LINE_LIMIT)
        detail, _ = CompleteContentCompiler._complete_sentence_excerpt(
            remainder or cleaned,
            104,
            maximum_extra=60,
        )
        if CompleteContentCompiler._canonical_role(focus) == "results":
            detail = re.sub(
                r"^(?:which|that)\s+(?=(?:achieves?|attains?|delivers?|outperforms?|reaches?|reports?|shows?|uses?)\b)",
                "The referenced baseline ",
                detail,
                flags=re.I,
            )
            if re.match(r"^\d+(?:\.\d+)?%", detail):
                detail = f"The referenced baseline records {detail}"
            detail = re.sub(r",\s+and\s+", " and ", detail, flags=re.I)
        if any(item.evidence_type == "limitation" for item in node.nodes):
            return f"边界：{detail}"
        if index == page_count - 1:
            return "综合前述证据形成核心判断，并将边界转化为下一步可验证行动。"
        return f"解读：{detail}"

    @staticmethod
    def _evidence_body(text: str) -> str:
        cleaned = text.strip(" #\t")
        cleaned = re.sub(
            r"^\s*\d+(?:\.\d+)+\.?\s+[^\r\n]{2,80}[\r\n]+",
            "",
            cleaned,
            count=1,
        )
        cleaned = SPACE.sub(" ", cleaned).strip()
        cleaned = PARENTHETICAL_CITATION.sub("", cleaned)
        bibliography_end = CompleteContentCompiler._bibliography_prefix_end(cleaned)
        if bibliography_end is not None:
            cleaned = cleaned[bibliography_end:].lstrip()
        cleaned = re.sub(r"^\d+(?:\.\d+)*\s*", "", cleaned)
        return cleaned

    @staticmethod
    def _canonical_role(focus: str | None) -> str:
        return ROLE_ALIASES.get(focus or "", focus or "")

    @staticmethod
    def _sentences(text: str) -> list[str]:
        cleaned = SPACE.sub(" ", text).strip()
        return [part.strip() for part in SENTENCE_BOUNDARY.split(cleaned) if part.strip()] or [cleaned]

    @staticmethod
    def _role_excerpt(text: str, focus: str | None) -> str:
        cleaned = CompleteContentCompiler._evidence_body(text)
        canonical = CompleteContentCompiler._canonical_role(focus)
        keywords = ROLE_KEYWORDS.get(canonical, ())
        sentences = CompleteContentCompiler._sentences(cleaned)
        if not keywords or len(sentences) == 1:
            return cleaned

        def score(sentence: str) -> tuple[int, int]:
            lowered = sentence.casefold()
            keyword_score = sum(keyword.casefold() in lowered for keyword in keywords) * 12
            metric_score = 0
            if canonical == "results":
                metric_score += len(re.findall(r"\b\d+(?:\.\d+)?%", sentence)) * 8
                metric_score += sum(
                    marker in lowered
                    for marker in ("outperform", "best overall", "increase", "decrease", "improve")
                ) * 8
            if canonical == "limitations":
                metric_score += sum(
                    marker in lowered
                    for marker in ("constraint", "inaccurate", "restricted", "trade-off")
                ) * 10
            return keyword_score + metric_score, min(len(sentence), 180)

        best_index = max(range(len(sentences)), key=lambda index: (*score(sentences[index]), -index))
        if score(sentences[best_index])[0] == 0:
            return cleaned
        return " ".join(sentences[best_index:])

    @staticmethod
    def _bibliography_prefix_end(text: str) -> int | None:
        cleaned = SPACE.sub(" ", text).strip()
        if not re.match(r"^[A-Z][A-Za-z'’-]+,\s*[A-Z]\.", cleaned):
            return None
        year = re.search(r"\((?:19|20)\d{2}[a-z]?\)\.\s*", cleaned[:240], re.I)
        return year.end() if year else None

    @staticmethod
    def _split_excerpt(text: str, limit: int) -> tuple[str, str]:
        cleaned = SPACE.sub(" ", text).strip()
        if len(cleaned) <= limit:
            return cleaned.rstrip(" ，,。.;；:："), ""
        prefix = cleaned[:limit + 1]
        cjk = sum("\u4e00" <= character <= "\u9fff" for character in prefix)
        meaningful = sum(character.isalnum() for character in prefix)
        boundary = limit
        minimum = max(8, int(limit * 0.35))
        clauses = [
            match.end() for match in re.finditer(r"[。！？.!?;；:：](?:\s+|$)", prefix)
            if match.end() >= minimum
        ]
        if clauses:
            boundary = clauses[-1]
        elif meaningful and cjk / meaningful < 0.35:
            spaces = [match.start() for match in re.finditer(r"\s+", prefix)]
            usable = [position for position in spaces if position >= minimum]
            if usable:
                boundary = usable[-1]
        head = cleaned[:boundary].rstrip(" ，,。.;；:：")
        tail = cleaned[boundary:].lstrip(" ，,。.;；:：")
        if tail and meaningful and cjk / meaningful < 0.35:
            words = head.split()
            deferred = []
            while len(words) > 1:
                token = words[-1].casefold().strip(".,;:()")
                if token not in TRAILING_CONNECTORS and not token.endswith(("'s", "’s")):
                    break
                deferred.insert(0, words.pop())
            if deferred:
                head = " ".join(words)
                tail = " ".join([*deferred, tail])
        return head, tail

    @staticmethod
    def _complete_sentence_excerpt(text: str, limit: int, *, maximum_extra: int) -> tuple[str, str]:
        cleaned = SPACE.sub(" ", text).strip()
        sentences = CompleteContentCompiler._sentences(cleaned)
        first = sentences[0] if sentences else ""
        if first and len(first) <= limit + maximum_extra:
            tail = cleaned[len(first):].lstrip(" ，,。.;；:：")
            return first.rstrip(" ，,。.;；:："), tail
        return CompleteContentCompiler._split_excerpt(cleaned, limit)

    @staticmethod
    def _clip_text(text: str, limit: int) -> str:
        return CompleteContentCompiler._split_excerpt(text, limit)[0]

    @staticmethod
    def _evidence_state(scene: str, allowed: tuple[str, ...]) -> str:
        preferred = "published" if "文献" in scene else "final" if any(token in scene for token in ("毕业", "结题", "会议")) else allowed[0]
        return preferred if preferred in allowed else allowed[-1]

    @staticmethod
    def _extract_figures(source_paths: list[Path], root: Path) -> tuple[list[dict], list[Path]]:
        skill_root = Path(__file__).resolve().parents[1]
        figures = []
        manifests = []
        for index, source in enumerate(path for path in source_paths if path.suffix.casefold() == ".pdf"):
            destination = root / f"source_{index + 1:02d}"
            subprocess.run(
                [sys.executable, str(skill_root / "scripts" / "extract_figures.py"), str(source), "--output-dir", str(destination)],
                cwd=skill_root,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            manifest = destination / "manifest.json"
            manifests.append(manifest)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            figures.extend(item for item in payload["items"] if item.get("accepted") and item.get("path"))
        return figures, manifests

    @staticmethod
    def _take_nearest_figure(figures: list[dict], page: int | None, *, max_distance: int) -> dict | None:
        if not figures:
            return None
        if page is None:
            return figures.pop(0)
        selected = min(figures, key=lambda item: abs(int(item.get("source_page", 0)) - int(page)))
        if abs(int(selected.get("source_page", 0)) - int(page)) > max_distance:
            return None
        figures.remove(selected)
        return selected

    @staticmethod
    def _page_figure(
        figures: list[dict],
        page: int | None,
        index: int,
        page_count: int,
        *,
        focus: str | None = None,
        claim: str = "",
    ) -> dict | None:
        if index in {0, page_count - 1}:
            return None
        if not figures:
            return None
        if page is None:
            return figures.pop(0)
        selected = min(figures, key=lambda item: abs(int(item.get("source_page", 0)) - int(page)))
        distance = abs(int(selected.get("source_page", 0)) - int(page))
        if distance > 3:
            return None
        canonical = CompleteContentCompiler._canonical_role(focus)
        if distance and canonical in {"contributions", "limitations", "future_work", "ending"}:
            caption = str(selected.get("caption", "")).casefold()
            claim_terms = {
                token
                for token in re.findall(r"[a-z][a-z0-9-]{4,}", claim.casefold())
                if token not in {"about", "after", "before", "could", "framework", "their", "there", "these", "through", "using", "which", "would"}
            }
            caption_terms = set(re.findall(r"[a-z][a-z0-9-]{4,}", caption))
            if not claim_terms.intersection(caption_terms):
                return None
        figures.remove(selected)
        return selected

    @staticmethod
    def _supporting_evidence(
        primary: EvidencePassage,
        passages: list[EvidencePassage],
        *,
        target: int = 3,
        maximum: int = 4,
    ) -> tuple[str, ...]:
        evidence_ids = list(dict.fromkeys(primary.evidence_ids))
        if len(evidence_ids) >= target:
            return tuple(evidence_ids[:maximum])
        primary_sources = {node.source_id for node in primary.nodes}

        def rank(item: EvidencePassage) -> tuple[int, int, int]:
            same_source = int(bool(primary_sources & {node.source_id for node in item.nodes}))
            if primary.page is None or item.page is None:
                distance = 999
            else:
                distance = abs(primary.page - item.page)
            typed = sum(node.evidence_type in {"method", "result", "limitation"} for node in item.nodes)
            return (-same_source, distance, -typed)

        for passage in sorted((item for item in passages if item is not primary), key=rank):
            if primary.page is not None and passage.page is not None and abs(primary.page - passage.page) > 2:
                continue
            for evidence_id in passage.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)
                if len(evidence_ids) >= target:
                    return tuple(evidence_ids[:maximum])
        return tuple(evidence_ids[:maximum])

    @staticmethod
    def _native_strategy(focus: str, index: int, page_count: int) -> str:
        focus = CompleteContentCompiler._canonical_role(focus)
        if index in {0, page_count - 1}:
            return "text_only"
        if focus in {"method", "methods", "research_inspiration", "next_action"}:
            return "native_diagram"
        if focus in {"experiments", "results", "data"}:
            return "native_diagram"
        return "native_diagram" if index % 2 else "text_only"

    @staticmethod
    def _split_claim(claim: str, count: int) -> list[str]:
        words = claim.split()
        if len(words) >= count:
            base, remainder = divmod(len(words), count)
            chunks = []
            offset = 0
            for index in range(count):
                size = base + int(index < remainder)
                chunks.append(" ".join(words[offset:offset + size]))
                offset += size
        else:
            size = max(1, math.ceil(len(claim) / count))
            chunks = [claim[index:index + size] for index in range(0, len(claim), size)][:count]
        return [*chunks, *("" for _ in range(count - len(chunks)))]

    @staticmethod
    def _process_steps(
        text: str,
        focus: str,
        claim: str,
        interpretation: str,
        transition: str,
    ) -> list[str]:
        candidates = []
        for sentence in CompleteContentCompiler._sentences(
            CompleteContentCompiler._role_excerpt(text, focus)
        ):
            cleaned = re.sub(r"^\d+\.\s*", "", sentence).strip(" ，,。.;；:：")
            cleaned = re.sub(r"\s+\d+$", "", cleaned).strip()
            cleaned = re.sub(r"\bthe proposed framework\b", "the framework", cleaned, flags=re.I)
            cleaned = re.sub(r"\bclearly\s+", "", cleaned, flags=re.I)
            if len(cleaned) > 105:
                that_clause = re.search(r"\s+that\s+", cleaned, flags=re.I)
                if that_clause is not None:
                    preceding = cleaned[:that_clause.start()].rstrip().split()[-1].casefold()
                    if preceding not in {"confirm", "confirms", "demonstrate", "demonstrates", "indicate", "indicates", "show", "shows"}:
                        cleaned = cleaned[:that_clause.start()].rstrip()
                cleaned = re.split(
                    r"\s+across\s+(?=(?:diverse|multiple)\b)|,\s+(?=(?:including|which|while|with)\b)",
                    cleaned,
                    maxsplit=1,
                    flags=re.I,
                )[0].rstrip(" ，,。.;；:：")
            meaningful = sum(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in cleaned)
            if meaningful >= 12 and cleaned not in candidates:
                candidates.append(CompleteContentCompiler._clip_text(cleaned, 120))
            if len(candidates) == 5:
                break
        fallbacks = [claim, interpretation.removeprefix("解读：").removeprefix("边界："), transition]
        for value in fallbacks:
            cleaned = value.strip(" ，,。.;；:：")
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)
            if len(candidates) >= 3:
                break
        return candidates[:5]
