# 内置 PPT 模板目录

用户有自定义模板时优先使用用户模板。没有模板时，使用以下稳定编号和短名称；不要让用户重复完整文件名。

| 编号 | 短名称 | 主要场景 | 正式 PowerPoint 资产 | 来源风格文件 |
|---|---|---|---|---|
| `T01` | 绿色科研 | 组会、开题、学术报告 | `T01_green_research.pptx` | `绿色-科研风格PPT模版.pptx` |
| `T02` | 蓝色科研 | 毕业答辩、课题进展、学术报告 | `T02_blue_research.pptx` | `蓝色-科研学术汇报通用模板_升级版.pptx` |
| `T03` | 蓝色答辩 | 开题、中期、毕业答辩 | `T03_blue_defense.pptx` | `蓝色-学术答辩多版式通用模板 (Academic Defense Multi-Layout Template).pptx` |
| `T04` | 项目申报 | 项目申报、比赛、中期与结题 | `T04_project_application.pptx` | `科研项目申报汇报模板.pptx` |
| `T05` | 红色通用 | 开题、中期、科研比赛 | `T05_red_general.pptx` | `红色-通用模版.pptx` |
| `T06` | 云大紫色 | 云南大学开题、中期、毕业答辩 | `T06_yunnan_purple.pptx` | `云大答辩PPT-紫色款.pptx` |
| `T07` | 云大红色 | 云南大学开题、中期、毕业答辩 | `T07_yunnan_red.pptx` | `云大答辩PPT-红色款.pptx` |
| `T08` | 云大蓝色 | 云南大学开题、中期、毕业答辩 | `T08_yunnan_blue.pptx` | `云大答辩PPT-蓝色款.pptx` |

接受 `T01`、`01`、`绿色科研`、`绿色模板` 等目录中登记的别名。机器目录位于 `template-catalog.json`，通过以下命令解析：

```powershell
python scripts/resolve_template.py T01 --json
```

编号只表示稳定选择键，不表示质量排序。用户可在选定模板后要求转换为学术蓝、科研绿、酒红、紫灰等预设配色；换色不改变原页面、槽位和图层。

`assets/templates` 保存来源包，`assets/powerpoint_templates` 保存正式目录副本。
T01 与 T03 不是风格近似稿：它们由指定来源包重新打包，完整保留 10/11 页、shape
结构、几何、字体、字号、位置、图片脚手架和版式原型，仅规范媒体包。目录报告位于
`compiled-template-report.json`。使用以下命令可重复编译并执行结构身份回归：

```powershell
python scripts/compile_bundled_source_templates.py
python scripts/validate_palette_identity.py original.pptx recolored.pptx
```
