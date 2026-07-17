# 内置 PPT 模板目录

用户有自定义模板时优先使用用户模板。没有模板时，使用以下稳定编号和短名称；不要让用户重复完整文件名。

| 编号 | 短名称 | 主要场景 | 标准 PowerPoint 资产 | 当前标准化状态 |
|---|---|---|---|---|
| `T01` | 绿色科研 | 组会、开题、学术报告 | `T01_green_research.pptx` | 语义编译、真实内容对象级 QA 与 PowerPoint 逐页视觉验收通过 |
| `T02` | 蓝色科研 | 毕业答辩、课题进展、学术报告 | `T02_blue_research.pptx` | 语义编译与标准模板 PowerPoint 验收通过；真实内容候选待题注修复后重建复验 |
| `T03` | 蓝色答辩 | 开题、中期、毕业答辩 | `T03_blue_defense.pptx` | 语义编译、真实内容对象级 QA 与 PowerPoint 逐页视觉验收通过 |
| `T04` | 项目申报 | 项目申报、比赛、中期与结题 | `T04_project_application.pptx` | 待语义编译，不得作为已验收模板发布 |
| `T05` | 红色通用 | 开题、中期、科研比赛 | `T05_red_general.pptx` | 待语义编译，不得作为已验收模板发布 |
| `T06` | 云大紫色 | 云南大学开题、中期、毕业答辩 | `T06_yunnan_purple.pptx` | 待语义编译，不得作为已验收模板发布 |
| `T07` | 云大红色 | 云南大学开题、中期、毕业答辩 | `T07_yunnan_red.pptx` | 待语义编译，不得作为已验收模板发布 |
| `T08` | 云大蓝色 | 云南大学开题、中期、毕业答辩 | `T08_yunnan_blue.pptx` | 待语义编译，不得作为已验收模板发布 |

接受 `T01`、`01`、`绿色科研`、`绿色模板` 等目录中登记的别名。机器目录位于 `template-catalog.json`，通过以下命令解析：

```powershell
python scripts/resolve_template.py T01 --json
```

编号只表示稳定选择键，不表示质量排序。用户可在选定模板后要求转换为学术蓝、科研绿、酒红、紫灰等预设配色；换色不改变原页面、槽位和图层。

`assets/templates` 保存来源包，`assets/powerpoint_templates` 保存标准目录副本，
`assets/template_specs` 保存机器可读语义规格。目录中的资产存在不等于 1.0 发布验收；
`template-catalog.json` 的 `standardization_status` 是当前真实状态。
T01、T02 与 T03 不是风格近似稿：它们由指定来源包重新打包，完整保留 10/9/11 页、shape
结构、几何、字体、字号、位置、图片脚手架和版式原型，仅规范媒体包。目录报告位于
`compiled-template-report.json`。其语义规格进一步记录页面原型、模块、子槽、完整删除
所有权、字体容量、页级/模块级媒体与模板身份。使用以下命令可重复编译和校验：

```powershell
python scripts/compile_bundled_source_templates.py
python scripts/validate_template_spec.py assets/template_specs/T01_green_research.semantic.json assets/template_specs/T02_blue_research.semantic.json assets/template_specs/T03_blue_defense.semantic.json
python scripts/validate_template_identity.py assets/template_specs/T01_green_research.semantic.json assets/template_specs/T02_blue_research.semantic.json
python scripts/validate_template_identity.py assets/template_specs/T02_blue_research.semantic.json assets/template_specs/T03_blue_defense.semantic.json
python scripts/validate_palette_identity.py original.pptx recolored.pptx
```

正式生成页的对象级验收必须同时提供语义规格和实际绑定清单：

```powershell
python scripts/validate_pptx.py deck.pptx --layout-plan layout_plan.json --semantic-spec template.semantic.json --object-manifest object_bindings.json --asset-root working --render-check required --render-engine powerpoint --output render_report.json
```

缺少绑定清单时，只能验证标准模板本身的所有权、重复对象、跨模块重叠和身份组件；
不能据此宣称媒体来源、空槽删除、字体绑定或样例残留已经通过。
