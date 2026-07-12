# python-pptx 常用操作速查

> 供 Phase 3 渲染时参考。编写 `render_pptx.py` 和调试 PPTX 问题时使用。

---

## 基础：打开与保存

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# 打开模板
prs = Presentation("template.pptx")

# 保存
prs.save("output.pptx")
```

## 幻灯片尺寸

```python
prs.slide_width   # EMU, 16:9 = 12192000 (13.33")
prs.slide_height  # EMU, 16:9 = 6858000  (7.5")
```

## 版式与创建幻灯片

```python
# 遍历版式
for i, layout in enumerate(prs.slide_layouts):
    print(f"L{i:02d}: {layout.name}")

# 按名称选版式创建幻灯片
layout = prs.slide_layouts.get_by_name("TWO_OBJECTS")
slide = prs.slides.add_slide(layout)

# 按索引选版式
slide = prs.slides.add_slide(prs.slide_layouts[3])
```

## 占位符操作

```python
# 遍历当前幻灯片的所有占位符
for ph in slide.placeholders:
    print(f"idx={ph.placeholder_format.idx}, "
          f"name='{ph.name}', type={ph.placeholder_format.type}, "
          f"pos=({ph.left},{ph.top}) size={ph.width}x{ph.height}")

# 按 idx 访问占位符
ph = slide.placeholders[10]  # idx=10 的占位符

# 填充标题文本
if ph.placeholder_format.idx == 0:  # TITLE typically idx 0
    ph.text = "我的标题"

# 填充正文
tf = ph.text_frame
tf.clear()  # 清除默认占位文字
p = tf.paragraphs[0]
p.text = "第一行 bullet"
p.font.size = Pt(16)
```

## 文本框文本操作（精细控制）

```python
from pptx.oxml.ns import qn

def set_run_font(run, zh_font="微软雅黑", en_font="Times New Roman", size=None, bold=False, color=None):
    """设置 run 的中英文字体"""
    rPr = run._r.get_or_add_rPr()
    rPr.set(qn('a:ea'), zh_font)    # 东亚字体
    rPr.set(qn('a:latin'), en_font)  # 拉丁字体
    if size:
        run.font.size = size
    run.font.bold = bold
    if color:
        run.font.color.rgb = color

# 多段落示例
tf = text_frame
tf.clear()

items = [("论点一", "支撑数据"), ("论点二", "支撑数据")]
for i, (main, sub) in enumerate(items):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = f"● {main}"
    p.font.size = Pt(16)
    p.space_after = Pt(4)
    # 子项
    p2 = tf.add_paragraph()
    p2.text = f"  — {sub}"
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)
    p2.space_after = Pt(12)
```

## 插入图片

```python
# 计算适配尺寸（锁定宽高比）
def fit_image_to_box(img_path, box_left, box_top, box_w, box_h):
    """返回 (left, top, width, height) 使图片等比例适配 box"""
    from PIL import Image
    img = Image.open(img_path)
    img_w, img_h = img.size
    img_aspect = img_w / img_h
    box_aspect = box_w / box_h

    if img_aspect > box_aspect:
        # 图更宽 → 以 box 宽度为准
        new_w = box_w
        new_h = int(box_w / img_aspect)
    else:
        # 图更高 → 以 box 高度为准
        new_h = box_h
        new_w = int(box_h * img_aspect)

    # 居中放置
    left = box_left + (box_w - new_w) // 2
    top = box_top + (box_h - new_h) // 2
    return left, top, new_w, new_h

# 插入图片到指定位置
left, top, w, h = fit_image_to_box(
    "figure.png",
    ph.left, ph.top, ph.width, ph.height
)
slide.shapes.add_picture("figure.png", left, top, w, h)
```

## 创建表格

```python
rows, cols = 5, 4
table_shape = slide.shapes.add_table(rows, cols,
    Inches(0.8), Inches(2.0), Inches(11.5), Inches(3.5))
table = table_shape.table

# 设置列宽
table.columns[0].width = Inches(3.0)
table.columns[1].width = Inches(3.0)

# 填充数据
for r in range(rows):
    for c in range(cols):
        cell = table.cell(r, c)
        cell.text = f"R{r}C{c}"
        for para in cell.text_frame.paragraphs:
            para.font.size = Pt(11)
            para.alignment = PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT
```

## 讲稿备注

```python
notes_slide = slide.notes_slide
notes_slide.notes_text_frame.text = "这是演讲备注内容…"
```

## 常用测量转换

```python
Inches(1)        # → 914400 EMU
Cm(2.54)         # → 914400 EMU (= 1 inch)
Pt(12)           # → 152400 EMU (= 12 * 12700)
Emu(914400)      # → 914400 EMU

# 反向：EMU → inches
inch_val = emu / 914400
```

## 主题色读取

```python
# 从 slide master 的 theme 中提取颜色
from lxml import etree
master = prs.slide_masters[0]
xml = master.element.xml
# 搜索 <a:clrScheme> 及其子元素
```

## 常见陷阱

1. **占位符 idx 不等于遍历顺序**：`slide.placeholders[i]` 中的 i 是占位符的 `idx` 属性，不是列表索引。
   需要用 `ph.placeholder_format.idx` 来判断身份。

2. **字体设置需要操作 XML**：`run.font.name` 只能设置一种字体。中英文字体分离需要通过 XML 分别设置 `a:ea` 和 `a:latin`。

3. **图片宽高比**：`add_picture()` 不会自动锁定宽高比，必须手动计算后再插入。

4. **模板版式中的占位符可能被用户删除**：渲染前应检查目标占位符是否仍然存在。

5. **SmartArt 不可读写**：python-pptx 无法解析或创建 SmartArt。如果模板含 SmartArt，只能跳过。

6. **SVG 不能直接插入**：python-pptx 不支持 SVG 格式。需要先转换为 PNG 或 EMF：
   ```bash
   # 使用 cairosvg（纯 Python，最轻量）
   pip install cairosvg
   python -c "import cairosvg; cairosvg.svg2png(url='input.svg', write_to='output.png', output_width=1920)"
   ```

7. **python-pptx 没有公开的幻灯片克隆 API**：不能只深拷贝 shape XML。图片、
   图表、超链接、媒体和标签通过 `rId` 关系引用；克隆时必须复制全部关系并将
   XML 中的旧 `rId` 映射到新 `rId`。使用本 skill 的 `scripts/pptx_utils.py`，
   不要重新实现不完整的克隆逻辑。

8. **不要按面积或遍历顺序替换文字**：模板导航、页脚和装饰标签也可能是大
   文本框。先运行 `parse_template.py`，再按实际 `slide_index + shape_id` 绑定。
