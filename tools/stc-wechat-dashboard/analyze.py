# -*- coding: utf-8 -*-
"""
救助儿童会公众号文本分析 + 主题提炼（可复现版）

输入：txt/ 目录下的公众号清洗文本（文件名格式：YYYY-MM-DD_标题.txt）
输出：dashboard 数据文件（data.json + 聚合 CSV）

用法：
  python analyze.py --txt-dir /path/to/txt --out-dir /path/to/dashboard
  python analyze.py  # 默认: txt -> dashboard-output (相对当前工作目录)

注意：本脚本只消费本地 txt 文件，不上传公众号原文。
"""
import os, re, json, collections, argparse
from pathlib import Path

import jieba

def parse_args():
    ap = argparse.ArgumentParser(description="救助儿童会公众号文本分析")
    ap.add_argument("--txt-dir", default=os.environ.get("STC_TXT_DIR", "txt"),
                    help="清洗后的 txt 目录（文件名 YYYY-MM-DD_标题.txt）")
    ap.add_argument("--out-dir", default=os.environ.get("STC_OUT_DIR", "dashboard-output"),
                    help="分析结果输出目录")
    return ap.parse_args()

ARGS = parse_args()
TXT_DIR = str(Path(ARGS.txt_dir).resolve())
OUT_DIR = str(Path(ARGS.out_dir).resolve())
os.makedirs(OUT_DIR, exist_ok=True)
jieba.setLogLevel(20)

# 标签规范（对齐 yihot 项目 industry/taxonomy.ts + topics.json）：
# ① 不含 "/" 符号；② 2–5 字；③ 单概念，不捆绑两个不同概念
#   （原「妇女与女童」→ 性别平等；「健康与营养」→ 营养健康；「减灾救灾与安全」→ 应急救援；
#    「数字素养与网络保护」→ 网络保护；「公益与募资」→ 募集筹款；「招聘与实习」→ 招募实习）
# 凡 yihot 已有同名主题/体裁标签的，直接沿用其措辞，便于日后并入 yihot 分类体系。
THEMES = [
    {"key": "child_protection", "label": "儿童保护", "color": "#E4572E",
     "keywords": ["儿童保护","保护儿童","拐卖","虐待儿童","虐待","家暴","家庭暴力","暴力",
                  "强制报告","一站式","儿童之家","儿童主任","司法保护","未成年人","性侵","性侵害",
                  "防拐","儿童安全","受虐","儿童福利","监护","儿童权益","儿童友好司法"]},
    {"key": "health_nutrition", "label": "营养健康", "color": "#17A398",
     "keywords": ["健康","营养","母乳","喂养","疫苗","肺炎","卫生","口腔","近视","洗手","早产",
                  "护理","保健","疾病","营养膳食","视力","牙齿","免疫","膳食","健康饮食","生长发育"]},
    {"key": "education", "label": "儿童教育", "color": "#3A86FF",
     "keywords": ["教育","早期发展","早教","学前","幼儿园","全纳教育","融合教育","玩中学","亲子阅读",
                  "阅读","绘本","学习","学校","教师","教学","课程","识字","数学","语言发展","艺术",
                  "音乐","托育","启蒙","入园","游戏化","儿童参与","儿童教育"]},
    {"key": "women_girls", "label": "性别平等", "color": "#FF5DA2",
     "keywords": ["妇女","女童","妈妈","母亲","性别","月经","经期","她职场","女性","平等","女孩",
                  "孕","产后","母乳","妇联","妇女节","国际女童日","母亲节","赋能女性","性别平等"]},
    {"key": "environment", "label": "环境保护", "color": "#2A9D8F",
     "keywords": ["气候","气候变化","气候危机","气候行动","减排","低碳","碳中和","碳排放","环保","生态",
                  "湿地","生物多样性","地球日","减碳","COP","净零","气候资金","气候公正","气候治理",
                  "垃圾分类","污染","自然"]},
    {"key": "disaster", "label": "应急救援", "color": "#E9C46A",
     "keywords": ["减灾","救灾","地震","洪水","防灾","应急","避难","台风","灾难","灾后","救援",
                  "防汛","暴雨","泥石流","消防","国际减灾日","韧性","受灾","赈灾","疫情","抗疫",
                  "寒冬","飓风","干旱","滑坡"]},
    {"key": "youth", "label": "青年发展", "color": "#8338EC",
     "keywords": ["青年","职业","就业","创业","技能","中职","职校","绿色职业","导师","职场","简历",
                  "面试","职业发展","就业支持","创新创业","青年发展","职业教育","职业生涯"]},
    {"key": "disability", "label": "残障融合", "color": "#FB8500",
     "keywords": ["残障","残疾","融合","自闭症","孤独症","特殊","听障","视障","康复","无障碍",
                  "个别化","学前融合","残障融合","融合就业"]},
    {"key": "parenting", "label": "亲子养育", "color": "#FFB703",
     "keywords": ["正向教养","亲子","家长","养育","教养","父母","育儿","打小孩","不打小孩","管教",
                  "亲子关系","陪伴","家庭教育","家长讲座","情绪"]},
    {"key": "digital", "label": "网络保护", "color": "#4361EE",
     "keywords": ["数字","网络","屏幕","手机","网课","网络安全","网络欺凌","数字素养","网络保护",
                  "上网","短视频","信息素养","网络性侵","网络素养","电子"]},
    {"key": "fundraising", "label": "募集筹款", "color": "#D62828",
     "keywords": ["募资","捐赠","捐款","慈善","善款","义卖","拍卖","月捐","筹款","资助","募捐",
                  "劝募","配捐","腾讯公益","公益项目","基金会","公益节","爱心"]},
    {"key": "advocacy", "label": "政策倡导", "color": "#6A4C93",
     "keywords": ["倡导","政策","公约","立法","联合国","COP","论坛","蓝皮书","研讨会","峰会","年会",
                  "儿童权利","发声","呼吁","意见","宣言","发布"]},
    {"key": "recruitment", "label": "招募实习", "color": "#8D99AE",
     "keywords": ["招聘","工作机会","招募","招实习生","实习机会","岗位","人才","招募令","招募啦",
                  "诚聘","实习","intern","实习生","顾问招募"]},
]
THEME_BY_KEY = {t["key"]: t for t in THEMES}
PRIORITY = ["child_protection","health_nutrition","education","women_girls","environment",
            "disaster","youth","disability","parenting","digital","fundraising","advocacy",
            "recruitment","other"]
PRIORITY_IDX = {k:i for i,k in enumerate(PRIORITY)}

BASE_STOP = ("的 了 和 是 在 就 都 而 及 与 着 或 一个 没有 我们 你们 他们 她们 以及 因为 所以 如果 但是 并且 "
           "同时 其中 进行 通过 对于 关于 这个 那个 这些 那些 已经 可以 需要 还是 就是 不是 一种 一些 "
           "一项 一名 一次 进一步 更加 持续 不断 成为 实现 推动 促进 表示 指出 认为 提出 开展 推进 工作 "
           "相关 有关 方面 情况 问题 内容 重点 全面 重要 近日 今天 此次 目前 来说 作为 根据 来自 记者 "
           "编辑 文章 全文 阅读 原标题 作者 来源 发布 公众号 微信 视频 点击 链接 图片 中国 社会 国家 "
           "大家 一起 可能 非常 还有 这样 本次 活动 项目 平台 让 也 还 把 被 给 等 中 上 下 后 前 内 "
           "将 并 对 为 从 到 以 之 其 该 各 多 小 大 新 年 月 日 时 个 位 名 项 次 条 份 "
           "自己 一样 这么 那么 什么 怎么 如何 我们 你们 他们 她们 这里 那里 现在 因为 所以 但是 "
           "通过 对于 关于 一个 一种 一些 一项 一名 一次 进一步 更加 持续 不断 成为 实现 推动 促进")
NOISE = ("及性 受训 文盲 病史 签署国 结论性 审议 始创 拥有者 上个世纪 水灾 黄经 齿槽 磨牙 饼铛 烤箱 "
         "小脚丫 脚丫 小豆 彩带 飞沫 野生动物 海内外 浩睿 门建林 四至 中端 区委 一山一水 积石山 蚌埠市 "
         "始创 拥有者 第四次 下面 原文 今年 毕竟 下周 太棒 公历 扫一扫 就近 独家 发生 中心 北京 原文 "
         "时为 七步 拍了拍 犯难 事不宜迟 右一 无遗 多边 布鲁塞尔 受限 业务主管 公历")
STOP = set(BASE_STOP.split()) | set(NOISE.split())

# 常见姓氏（用于剔除人名词频噪声）
_SURNAME_STR = ("王李张刘陈杨黄赵周吴徐孙朱马胡郭何高林郑谢罗梁宋唐许韩冯邓曹彭曾"
               "萧田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢傅钟姜崔谭廖范汪陆金石"
               "戴贾韦夏邱方侯邹熊孟秦白江阎薛尹段雷黎史龙陶贺顾毛郝龚邵万钱严覃"
               "武戚莫孔向汤房常康施游洪甘文卜屠池鞠鹿荣靳阴松蓝刁裘褚廉桑冀赖简景管华")
SURNAMES = set(_SURNAME_STR)
_KEEP = set()  # 保留词（总体高频词 + 主题关键词），在分词后填充
def is_name(w):
    # 2-3 字且首字为常见姓氏，且不在保留词中 -> 视为人名
    if not (2 <= len(w) <= 3): return False
    if w[0] not in SURNAMES: return False
    if w in _KEEP: return False
    return True

# ----------------------------------------------------------
files = sorted([f for f in os.listdir(TXT_DIR) if f.endswith(".txt") and not f.startswith(".workbuddy")])
pat = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_(.*)$")
from datetime import date as D

articles = []
for doc_id, f in enumerate(files, 1):
    name = f[:-4]
    m = pat.match(name); date=None; year=None; title=name
    if m:
        y,mo,d,ttl = m.groups()
        try:
            date = D(int(y),int(mo),int(d)); year=int(y); title=ttl
        except Exception: pass
    try:
        with open(os.path.join(TXT_DIR,f),"r",encoding="utf-8-sig") as fh: text=fh.read()
    except Exception:
        with open(os.path.join(TXT_DIR,f),"r",encoding="gb18030",errors="ignore") as fh: text=fh.read()
    text = re.sub(r"\s+"," ",text).strip()
    articles.append({"doc_id":doc_id,"file":f,"date":date.isoformat() if date else None,
                     "year":year,"title":title,"text":text,"char_n":len(text)})
print("读取文章:", len(articles))

def classify(text):
    hits={}
    for t in THEMES:
        c=sum(text.count(kw) for kw in t["keywords"])
        if c>0: hits[t["key"]]=c
    return hits

for a in articles:
    hits=classify(a["text"])
    if hits:
        best=sorted(hits.items(),key=lambda kv:(-kv[1],PRIORITY_IDX.get(kv[0],99)))[0][0]
        a["primary_theme"]=best
        a["themes"]=sorted(hits.keys(),key=lambda k:(-hits[k],PRIORITY_IDX.get(k,99)))
    else:
        a["primary_theme"]="other"; a["themes"]=["other"]
if not any(t["key"]=="other" for t in THEMES):
    THEMES.append({"key":"other","label":"其他","color":"#B0B0B0","keywords":[]})
    THEME_BY_KEY["other"]={"key":"other","label":"其他","color":"#B0B0B0"}

# ----------------------------------------------------------
# 单遍分词：累计 总体 / 年度 / 主题 的词频与文档频次
# ----------------------------------------------------------
overall_counter = collections.Counter()
year_counter = collections.defaultdict(collections.Counter)
year_df = collections.defaultdict(collections.Counter)      # year -> word -> 文档数
theme_counter = collections.defaultdict(collections.Counter)
theme_df = collections.defaultdict(collections.Counter)     # theme -> word -> 文档数

def good(w):
    return (len(w)>=2 and w not in STOP and not re.fullmatch(r"[0-9a-zA-Z%．.·]+", w))

for a in articles:
    toks=[w for w in jieba.cut(a["text"]) if good(w)]
    overall_counter.update(toks)
    yr = a["year"] if a["year"] else "未知"
    year_counter[yr].update(toks)
    uniq=set(toks)
    for w in uniq: year_df[yr][w]+=1
    for tk in a["themes"]:
        theme_counter[tk].update(toks)
        for w in uniq: theme_df[tk][w]+=1

sum_all = sum(overall_counter.values()) or 1
overall_top=[{"word":w,"n":n} for w,n in overall_counter.most_common(80)]
_KEEP |= set(w["word"] for w in overall_top)
_KEEP |= set(kw for t in THEMES for kw in t["keywords"])

years_sorted=sorted([y for y in year_counter if y!="未知"])
# 年度 TF-IDF 特征词：df>=4 且 年度词频>=6，按 (年占比/全局占比) 排序
tfidf_year={}
for yr in years_sorted:
    sy=sum(year_counter[yr].values()) or 1
    scores=[]
    for w,n in year_counter[yr].items():
        if is_name(w): continue
        if year_df[yr][w] < 8 or n < 10: continue
        ov=overall_counter[w] or 1
        ratio=(n/sy)/(ov/sum_all)
        scores.append((w,round(ratio,3),n))
    scores.sort(key=lambda x:-x[1])
    tfidf_year[yr]=[{"word":w,"score":s,"n":n} for w,s,n in scores[:12]]

# 主题代表词：df>=4 且 主题词频>=6，按 lift 排序
theme_top_words={}
for t in THEMES:
    k=t["key"]; st=sum(theme_counter[k].values()) or 1
    scores=[]
    for w,n in theme_counter[k].items():
        if is_name(w): continue
        if theme_df[k][w] < 5 or n < 6: continue
        ov=overall_counter[w] or 1
        lift=(n/st)/(ov/sum_all)
        scores.append((w,n,round(lift,3)))
    scores.sort(key=lambda x:-x[2])
    theme_top_words[k]=[{"word":w,"n":n,"score":s} for w,n,s in scores[:15]]

# 主题 × 年份（主主题）
primary_counter=collections.Counter(a["primary_theme"] for a in articles)
theme_year_primary=collections.defaultdict(collections.Counter)
for a in articles:
    theme_year_primary[a["primary_theme"]][a["year"] if a["year"] else "未知"]+=1

# 主题共现
cooc=collections.Counter()
for a in articles:
    ts=a["themes"]
    for i in range(len(ts)):
        for j in range(i+1,len(ts)):
            cooc[(ts[i],ts[j])]+=1

yearly=[]
for y in years_sorted:
    ys=[a for a in articles if a["year"]==int(y)]
    cs=sum(a["char_n"] for a in ys)
    yearly.append({"year":int(y),"count":len(ys),"total_char":cs,
                   "avg_char":round(cs/len(ys),1) if ys else 0})

theme_summary=[]
for t in THEMES:
    k=t["key"]; cnt=primary_counter.get(k,0)
    by_year={str(y):theme_year_primary[k].get(y,0) for y in years_sorted}
    theme_summary.append({"key":k,"label":t["label"],"color":t["color"],"count":cnt,
                          "pct":round(100*cnt/len(articles),1),"by_year":by_year,
                          "top_words":theme_top_words.get(k,[])})

data={"meta":{"total":len(articles),"year_min":int(years_sorted[0]) if years_sorted else None,
              "year_max":int(years_sorted[-1]) if years_sorted else None,
              "theme_count":len(THEMES),"vocab_size":len(overall_counter),"generated":"2026-10-16"},
      "yearly":yearly,"themes":theme_summary,"overall_top_words":overall_top,
      "tfidf_year":tfidf_year,
      "cooccurrence":[{"a":a,"b":b,"n":n} for (a,b),n in cooc.most_common(150)],
      "theme_keys":{t["key"]:t["label"] for t in THEMES},
      "articles":[{"id":a["doc_id"],"date":a["date"],"year":a["year"],"title":a["title"],
                   "primary":a["primary_theme"],"themes":a["themes"]} for a in articles]}
with open(os.path.join(OUT_DIR,"data.json"),"w",encoding="utf-8") as fh:
    json.dump(data,fh,ensure_ascii=False,indent=1)
print("data.json 完成")

import csv
def write_csv(path,rows,header):
    with open(path,"w",encoding="utf-8-sig",newline="") as fh:
        w=csv.writer(fh); w.writerow(header)
        for r in rows: w.writerow(r)
arows=[[a["doc_id"],a["date"] or "",a["year"] or "",a["title"],a["primary_theme"],
        ";".join(a["themes"]),a["char_n"]] for a in articles]
write_csv(os.path.join(OUT_DIR,"articles_theme.csv"),arows,
          ["doc_id","date","year","title","primary_theme","all_themes","char_n"])
write_csv(os.path.join(OUT_DIR,"theme_summary.csv"),
          [[t["key"],t["label"],t["count"],t["pct"]] for t in theme_summary],["key","label","count","pct"])
write_csv(os.path.join(OUT_DIR,"freq_overall.csv"),
          [[w["word"],w["n"]] for w in overall_top],["word","n"])
frows=[]
for yr,lst in tfidf_year.items():
    for it in lst: frows.append([yr,it["word"],it["score"],it["n"]])
write_csv(os.path.join(OUT_DIR,"tfidf_year.csv"),frows,["year","word","score","n"])
crows=[[x["a"],THEME_BY_KEY.get(x["a"],{}).get("label",x["a"]),x["b"],
        THEME_BY_KEY.get(x["b"],{}).get("label",x["b"]),x["n"]] for x in data["cooccurrence"]]
write_csv(os.path.join(OUT_DIR,"cooccurrence.csv"),crows,["theme_a","label_a","theme_b","label_b","n"])
print("CSV 完成。")
print("主主题分布:")
for k,c in primary_counter.most_common():
    print(f"  {THEME_BY_KEY.get(k,{}).get('label',k)}: {c}")
