# 救助儿童会公众号文本分析（可复现版）

本目录是救助儿童会微信公众号历史文章的**文本分析与主题提炼复现流水线**。

> **数据边界：本目录只包含分析代码与静态资源，不含公众号原文。**
> 原文（`txt/`、`html/`、`txt_merged/`）不入库、不上传。
> 运行分析前，需要自行提供清洗后的 txt 语料目录。

## 做什么

1. 读取清洗后的公众号文章 txt（文件名格式：`YYYY-MM-DD_标题.txt`）
2. 用 jieba 分词，做**总体高频词、年度 TF-IDF 特征词、主题代表词、主题共现**等分析
3. 用关键词词典做**多标签主题归类**（13 个使命主题 + 其他，标签对齐 `industry/taxonomy.ts`）
4. 输出 `data.json` + 聚合 CSV（主题分布、高频词、年度特征词、共现表、文章主题表）
5. 由 `data.json` 生成**自包含交互式 HTML dashboard**（ECharts，离线可用）

## 文件

| 文件 | 作用 |
| --- | --- |
| `analyze.py` | 核心分析：读 txt → 分词 → 主题归类 → 输出 `data.json` 与 CSV |
| `build_dashboard.py` | 把 `data.json` 内联进单文件 `index.html`（ECharts + logo） |
| `selftest.js` | Node 无头冒烟测试：用 stub DOM/ECharts 验证 dashboard 逻辑 |
| `logo_stc.svg` | 救助儿童会官方 logo（base64 内联进 HTML，离线可用） |
| `echarts.min.js` | ECharts 离线副本（dashboard 优先用它，失败再回退 CDN） |

## 环境

- Python 3.9+
- 依赖：`jieba`（其余为 Python 标准库）
- Node（仅运行 `selftest.js` 冒烟测试时需要）

```bash
pip install "jieba>=0.42"
```

## 快速开始（完整复现）

```bash
# 1) 分析（--txt-dir 指向你本地的清洗语料目录；--out-dir 是输出目录）
python analyze.py --txt-dir /path/to/txt --out-dir /path/to/dashboard-output

# 2) 生成 dashboard（--data 指向上一步的 data.json）
python build_dashboard.py --data /path/to/dashboard-output/data.json \
                          --out /path/to/dashboard-output/index.html
```

默认值（不传参时）：
- `--txt-dir` 默认 `txt`（或环境变量 `STC_TXT_DIR`）
- `--out-dir` 默认 `dashboard-output`（或 `STC_OUT_DIR`）
- `--data` 默认 `dashboard-output/data.json`（或 `STC_DATA`）
- `--out` 默认 `dashboard-output/index.html`（或 `STC_HTML`）
- `--site`：生成带「← 回到关于」返回条的站点版本（对应部署到 yihot 的 `/about/dashboard`）

## 冒烟测试

```bash
node selftest.js
```

在无浏览器环境下用 Node stub 驱动 `build_dashboard.py` 生成的 JS 逻辑，验证主题数、文章数、检索过滤、结论渲染等关键路径，不依赖 ECharts。

## 输出说明

`analyze.py` 在 `--out-dir` 下写出：

- `data.json`：dashboard 数据源（元信息、年度统计、主题汇总、高频词、TF-IDF、共现、文章清单）
- `articles_theme.csv`：每篇文章的主主题与全部标签
- `theme_summary.csv`：主题分布
- `freq_overall.csv`：总体高频词
- `tfidf_year.csv`：年度特征词
- `cooccurrence.csv`：主题共现

`build_dashboard.py` 在 `--out` 写出自包含的 `index.html`。

## 自动化提示（供 AI 操作）

- 流水线是两个独立脚本，可顺序调用、可重复执行，幂等覆盖输出。
- 输入语料目录是**唯一外部依赖**；不提供该目录则无法运行，不会自动联网抓取。
- 输出目录建议放在仓库外（如 `/tmp` 或非 Git 目录），避免把生成产物误提交。
- 标签体系（`THEMES`、颜色）与 `industry/taxonomy.ts`、`industry/topics.json` 保持一致；如需新增主题，先在 `industry/taxonomy.ts` 对齐措辞，再同步本目录 `THEMES`。
