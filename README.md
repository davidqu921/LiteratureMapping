# LiteratureMapping 使用说明

本项目把“每篇论文有哪些属性”的 CSV 转为属性组之间的两两交叉表：每个格子显示同时被标记为这两个属性的论文引用，或这些论文的数量。它不读取论文全文，也不会判断人工分类是否正确。

## 这次已经生成的结果

输入：`data/lit-map 2026s sycophancy - FINAL MAP.csv`，31 篇论文，13 个属性。

- `output/final_map/main.pdf`：5 页检查稿，前 3 页每页一组热图及引用表，后 2 页为 Crossref 真实元数据生成的参考文献。
- `output/final_map/main_heatmaps.pdf`：1 页数量热图，包含全部三组交叉表。
- `output/final_map/overleaf.zip`：可上传 Overleaf 的 LaTeX 源码包。
- `output/final_map/report.json`：识别出的分组、各属性计数、缺失标记论文及运行配置。

PDF 是本次实际编译的产物。重新运行 Python 只会更新源码、CSV、报告和 ZIP；需要重新编译 LaTeX 才能更新 PDF。

第一组在原 CSV 中没有组名，配置暂命名为 `Evaluation method`（评估方式），应由团队确认。31 篇中有 12 篇在这一组没有任何标记，具体 DOI 见报告的 `unmarked_papers`。另外两组每篇都有至少一个标记。

## LaTeX、BibTeX、Overleaf 分别是什么

- `.tex`：表格和论文的排版源码。例如 `\cite{10.1145/3772318.3790934}` 会排版成文献编号。
- `.bib`：结构化参考文献数据库，包含引用键、作者、标题、年份、会议或期刊等。引用键必须与 CSV 的 `Key` 一致。
- `.pdf`：LaTeX 编译后的可阅读成品。
- Overleaf：在线编辑和编译这些文件的工具。它不是 CSV 分析器；这里先运行 Python 生成 `.tex`，再编译。

教授这段话的工作重点是先把 FINAL MAP 导出后生成第一批可讨论的地图，调整表格尺寸、准备参考文献；进一步自动化可以随后做。这里的地图是交叉矩阵表格，不是地理地图，也不是自动生成的文献综述正文。

## 输入结构约定

使用 UTF-8 CSV（允许 BOM），英文逗号分隔；含逗号的标题按标准 CSV 用双引号包住。每行列数相同；数据一行一篇论文；完全空白的数据行忽略。

当前 FINAL MAP 的结构：

| 位置 | 内容 | 处理方式 |
| --- | --- | --- |
| 第 1 行 | 元数据列名、属性组名称 | `URL`、`Title`、`Key`；组名仅放在该组起始列，后续留空 |
| 第 2 行 | 属性名称 | 去除首尾空格后使用 |
| 第 3 行 | 属性解释 | 保留在原 CSV，跳过，不作为论文 |
| 第 4 行起 | 每篇论文的元数据与标记 | 当前共 31 行 |
| A–C 列 | URL、Title、Key | `Key` 必填且唯一；本文件均为 DOI |
| D 列 | 空白分隔列 | 必须为空 |
| E–G 列 | 评估方式（暂定组名） | Human - Specialist、Human - Authors、AI - prompted |
| H–L 列 | Definition of sycophancy | Hallucination Agreement、Bias Agreement、Obsequiousness、Stance Change、Failure to challenge/trying to get along |
| M–Q 列 | Outcomes | None、User opinion、User action、System performance、User performance |

默认 `X`/`x` 表示标记，空白表示未标记。首尾空格会清理。`?`、`Yes`、`0` 等未经配置的值会报错，避免误算；可在 JSON 的 `positive_values`、`negative_values` 中显式配置其他取值。

空白并不证明论文没有该属性，也不自动转换成 `None`。`Outcomes / None` 本身是一个独立属性，原描述指“只测量 sycophancy，没有测量其影响”。一篇论文可在同一组勾选多项，因此格子计数和行列合计不能当作独立论文数。

引用键仅接受英文字母、数字和 `: . _ / -`。重复或空引用键、行宽错误、未知标记、未分组属性、空组、同组属性重名都会报错。不同组可以使用相同属性名，内部按列区分，不会混在一起。

## 分组配置与扩展

`configs/final_map.json` 的行号从 1 开始：`metadata_header_row=1`、`group_header_row=1`、`attribute_header_row=2`、`data_start_row=4`。

脚本沿第 1 行读取组名并向右延续，遇到下一个非空组名时切换组。这对应 Google Sheets 合并组标题导出后的常见结构。新增属性时，在第 2 行插入列并保留所在组的标题结构即可；不再改 Python 切片。

缺失组名无法凭内容可靠推断。当前第一组使用配置的 `unnamed_group_title`，并始终在报告中提醒；`group_titles` 把两个很长的原组名映射为短标题。如果要增加多个没有组名的组，先补齐组标题，或采用显式 `groups` 配置。

单行表头 CSV 没有分组信息，需要像 `configs/sample.json` 一样用 `groups` 指定每组名称及属性列表。示例为 7 个 Population、4 个 Evaluation、5 个 Intervention 属性。默认无参数运行使用该示例配置。

## 运行方法

生成器只用 Python 标准库，不需要安装第三方依赖。已在 Python 3.14.6 下运行验证。

在正常配置 Python 的终端：

```powershell
Set-Location 'D:\Summer_Project_2026\LiteratureMapping'
python .\csv_to_latex.py '.\data\lit-map 2026s sycophancy - FINAL MAP.csv' --config .\configs\final_map.json --out .\output\final_map
```

本机 `python` 当前指向不可用的 WindowsApps 别名；本次实际使用的可执行文件是：

```powershell
$litPython = 'C:\Users\david\AppData\Roaming\uv\python\cpython-3.14.6-windows-x86_64-none\python.exe'
Set-Location 'D:\Summer_Project_2026\LiteratureMapping'
& $litPython .\csv_to_latex.py '.\data\lit-map 2026s sycophancy - FINAL MAP.csv' --config .\configs\final_map.json --out .\output\final_map
& $litPython .\csv_to_latex.py  # 原始 sample 数据，输出到 output/sample
& $litPython -m unittest -v
```

显式传入的相对路径相对于终端当前目录。输出目录会自动创建；再次运行会覆盖同名生成文件，所以不要把人工编辑只保存在生成的 `.tex` 中。人工核实的 `references.bib` 是例外，脚本不会覆盖它。

## 输出样式与含义

| 文件前缀 | 行属性 | 列属性 | 数据格数 |
| --- | --- | --- | --- |
| `map_01` | Evaluation method | Definition of sycophancy | 3 × 5 |
| `map_02` | Evaluation method | Outcomes | 3 × 5 |
| `map_03` | Definition of sycophancy | Outcomes | 5 × 5 |

每组生成四个文件：

- `_citations.tex`：格子里列出匹配论文的引用编号；无匹配用横线。
- `_heatmap.tex`：格子里显示数量，紫色深度为 `100 × 格子论文数 / 全部论文数`，这次分母为 31。所有表使用同一比例，无匹配为白色的 0。
- `_counts.csv`：数量矩阵，可在 Excel 中复核。
- `_keys.csv`：每格对应的原始引用键，用分号分隔，可追溯到输入论文。

例如 `map_03` 的 `Stance Change × System performance` 是 5：有 5 篇论文同时在这两个属性上标记了 X。不是 5 次实验、5 个参与者或影响大小。

LaTeX 使用 `tabularx` 按 `\linewidth` 分配宽度、自动换行；不再给每列固定 9cm。完整检查稿采用 A4 横向；纯热图稿采用 A4 纵向。它们是讨论用布局，不是某个 workshop 的正式模板。列数大幅增加或移入狭窄的双栏模板时，仍需要拆表、使用跨栏 `table*` 或调整标题。

## Overleaf 使用方法

1. 上传 `output/final_map/overleaf.zip` 为新项目。
2. Main document 选择 `main.tex`（引用表 + 热图 + 参考文献），或 `main_heatmaps.tex`（仅热图）。
3. 编译器选择 pdfLaTeX，然后 Recompile。
4. 放入正式论文时，把所需 `map_*.tex` 和已核实的文献库复制到论文项目，通过 `\input{map_03_heatmap.tex}` 等插入。导言区需要 `tabularx`、`array`、`xcolor` 的 `table` 选项；引用命令与正式模板的文献系统保持一致。

官方说明：[上传项目](https://docs.overleaf.com/managing-projects-and-files/uploading-a-project)、[使用 .bib 文件](https://docs.overleaf.com/citing-and-references/working-with-.bib-files)。

本地编译需安装 LaTeX；本次复用了工作区已有 TinyTeX：

```powershell
$litTex = 'D:\Summer_Project_2026\.tmp\lak27-tex\TinyTeX\bin\windows'
Set-Location 'D:\Summer_Project_2026\LiteratureMapping\output\final_map'
& "$litTex\pdflatex.exe" -interaction=nonstopmode -halt-on-error main.tex
& "$litTex\bibtex.exe" main
& "$litTex\pdflatex.exe" -interaction=nonstopmode -halt-on-error main.tex
& "$litTex\pdflatex.exe" -interaction=nonstopmode -halt-on-error main.tex
& "$litTex\pdflatex.exe" -interaction=nonstopmode -halt-on-error main_heatmaps.tex
```

## Crossref 真实 BibTeX（2026-10-07 已完成）

31/31 篇均已从 Crossref 免费公共 API 下载真实 BibTeX 和 JSON 元数据。两个响应中的 DOI 都与输入匹配，31 条均含标题、作者、年份及会议/期刊字段。23 个 CSV 标题与返回标题在清理标点大小写后相同，8 个是返回完整标题的前缀；无其他标题差异。没有用生成模型补造书目信息。

下载脚本 `fetch_bibtex.py` 仅使用 `https://api.crossref.org` 的 HTTPS GET：无账户、无密钥、无付款，不发送私人文件、邮箱或属性编码，仅发送 DOI 和普通软件标识。串行请求、至少间隔 1 秒，处理限流/临时错误，保留缓存；第二次运行可完全从缓存重建。Crossref 会如一般网络服务一样看到请求 DOI 和网络地址。

免费公共接口与付费 Metadata Plus 是分开的。本流程未使用 Plus。来源：[Crossref 访问说明](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)、[官方公共 API 免费说明](https://github.com/CrossRef/rest-api-doc/blob/master/api_tips.md)、[BibTeX 转换说明](https://support.crossref.org/hc/en-us/articles/213673586-Content-negotiation)。

输出目录中：

- `crossref_cache/`：31 个原始 `.bib`、31 个 JSON 响应及各自来源 URL、抓取 UTC 时间和 SHA-256。未改动服务返回内容。
- `references_crossref.bib`：合并真实 BibTeX，只把引用键改为 CSV 的 DOI。
- `references_crossref_latex.bib`：同一元数据的排版兼容版。字段统一加花括号、保护标题大小写、把月份写为全称；解决服务返回 `June`、`July`、`Sept` 时 BibTeX 未定义月份宏的问题。
- `references.bib`：当前地图实际使用的兼容版，已包含在更新的 `overleaf.zip` 中。
- `crossref_audit.csv`、`crossref_report.json`：完整标题、年份、作者数量、场所、DOI 核查和失败记录；本次无失败。
- `references_draft.bib`：仅作为无真实库时的后备；当前 `main.tex` 已使用 `references.bib`。

复现下载和安装（在项目根目录，用上文 `$litPython` 或正常的 `python`）：

```powershell
& $litPython .\fetch_bibtex.py '.\data\lit-map 2026s sycophancy - FINAL MAP.csv'
# 下一行会替换当前使用的文献库；若自行编辑过 references.bib，请先保留自己的版本。
Copy-Item -LiteralPath '.\output\final_map\references_crossref_latex.bib' -Destination '.\output\final_map\references.bib'
& $litPython .\csv_to_latex.py '.\data\lit-map 2026s sycophancy - FINAL MAP.csv' --config .\configs\final_map.json --out .\output\final_map
& $litPython .\analyze_map.py '.\data\lit-map 2026s sycophancy - FINAL MAP.csv'
```

随后按上文命令重新编译；建议 pdfLaTeX 加 `-no-shell-escape`。下载脚本不会覆盖 `references.bib`；只有显式复制步骤替换它。任一 DOI 下载/核查失败时，保存错误报告而不替换合并库。缓存原样保留；若要重新查询某条，先备份并移走该 DOI 对应缓存条目。

这是 Crossref 登记元数据及其 BibTeX 转换结果，不保证与出版方网页导出逐字相同；尚未逐篇以论文 PDF 独立复核作者和页码，也未重新判断属性分类。

## 热图 findings

详见 [FINDINGS.md](FINDINGS.md)：含建议优先强调的三个发现、中英文措辞、解释边界及可直接修改的英文结果段落。`analyze_map.py` 按论文去重生成 `findings_evidence.json`（包含各项 DOI 列表及输入哈希）和 `findings_counts.csv`。

核心结果：15 篇标记至少一种用户结果，12 篇标记系统表现，仅 1 篇两者均标记；用户表现仅 4/31；不同定义对应的结果指标覆盖不均。联合覆盖是从逐篇 CSV 计算的，不能从热图简单相加得到。

## 原项目检查结果与本次修正

原 `csv_to_latex.py` 无命令行参数，写死读取 `sample_lit_map.csv`，使用单行表头和小写 `key`，只接受精确大写 `X`，不能直接读取 FINAL MAP 的三行表头。

原脚本在临时目录用 sample 实际运行成功，生成六个 `.txt` 表格片段，但存在以下问题：

- `fieldnames[1:7]` 实际只有 6 个属性，下一组却从索引 8 开始，漏掉 `Accessability`。
- 固定列宽 9cm，行标题宽 10cm/15cm，不适合普通论文页宽。
- 从未出现 X 的属性不会进入字典，生成相关表格时可能报 `KeyError`。
- `files/generate_tables.tex` 引用 `table1_data` 等文件，和脚本实际生成的文件名不同；所需 `references-mapping.bib` 也不在仓库中。
- 旧模板使用 A0 海报配置。原 `files/generated_tables.pdf` 是仓库已有产物，不是这次 FINAL MAP 的结果。

本次修正了分组、空属性、大小写/空格、LaTeX 特殊字符和输出衔接问题，增加了输入校验、可审计 CSV、可编译主文件、ZIP 打包和配置文件。原输入、旧表格片段及旧 PDF 均未改动。

验证包括 12 个自动化测试：原地图的 55 格逐一核对、分组与异常输入回归；BibTeX 解析、DOI 匹配、缓存、重定向限制、排版兼容；findings 的互斥分区及关键计数。两份 FINAL MAP PDF 均经过实际编译和排版检查。

## 与团队讨论的下一步

先确认第一组名称，以及 12 篇未标记论文的评估方式编码；对拟突出 findings 的关键论文再核对原文。若篇幅只有 1–2 页，可优先考虑“定义 × 结果指标”地图及两条主发现；若有 3–4 页，再增加其他地图及简短综合讨论。具体选表和篇幅仍应按团队研究问题与投稿模板决定。
