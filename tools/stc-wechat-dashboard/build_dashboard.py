# -*- coding: utf-8 -*-
"""生成自包含交互式 HTML dashboard（把 data.json 内联，图表库优先用同目录本地文件，离线可用）。

用法：
    python build_dashboard.py            # 生成 index.html
    python build_dashboard.py --site     # 生成 index.html，并带上「回到关于」返回条（部署到 yihot 时用）

图表库查找顺序：同目录 echarts.min.js → CDN（bootcdn/jsdelivr/unpkg）。
"""
import os, json, base64, sys, argparse

def parse_args():
    ap = argparse.ArgumentParser(description="由 data.json 生成自包含 HTML dashboard")
    ap.add_argument("--data", default=os.environ.get("STC_DATA", "dashboard-output/data.json"),
                    help="analyze.py 产出的 data.json 路径")
    ap.add_argument("--out", default=os.environ.get("STC_HTML", "dashboard-output/index.html"),
                    help="生成的 HTML 输出路径")
    ap.add_argument("--site", action="store_true", default=os.environ.get("STC_SITE", "").lower() in ("1","true","yes"),
                    help="生成带返回条的站点模式")
    return ap.parse_args()

def serialize_inline_json(obj):
    """Serialize JSON safely for embedding inside an inline <script> tag."""
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def main():
    args = parse_args()
    base = os.path.dirname(os.path.abspath(__file__))
    for_site = args.site
    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)
    data_js = serialize_inline_json(data)

    # 官方 Save the Children logo（从 savethechildren.net 获取，base64 内联，离线可用）
    logo_path = os.path.join(base, "logo_stc.svg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as lf:
            logo_b64 = base64.b64encode(lf.read()).decode("ascii")
        logo = '<img class="logo" src="data:image/svg+xml;base64,%s" alt="Save the Children">' % logo_b64
    else:
        logo = '<span class="logo" style="width:120px;height:38px;background:rgba(255,255,255,.25);border-radius:6px;display:inline-block"></span>'

    # 返回条的 href 不写死部署前缀：页面可能挂在 /、/yihot/ 或别的路径下，
    # 由 location.pathname 去掉末尾的 about/dashboard 再拼 /about，三种情况都对。
    # （file:// 打开时这一条是 hidden 的，也用不上。）
    backbar = (
        '<a class="back" id="back-to-about" href="/about">← 回到关于</a>'
        '<script>document.getElementById("back-to-about").href='
        'location.pathname.replace(/\\/?about\\/dashboard\\/?$/,"")+"/about";</script>'
        if for_site else '<a class="back" href="/about" hidden>← 回到关于</a>'
    )
    return args, data_js, logo, backbar

HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>救助儿童会公众号内容分析 · 2014–2026</title>
<style>
  :root{
    --bg:#f5f7fa; --card:#ffffff; --ink:#1a2530; --sub:#6b7885; --line:#e6ebf1;
    --accent:#E4002B; --accent2:#008C95; --soft:#f2f6fa; --r:16px;
  }
  *{box-sizing:border-box;}
  html{-webkit-text-size-adjust:100%;}
  body{margin:0;background:var(--bg);color:var(--ink);line-height:1.65;
    font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB",-apple-system,Segoe UI,Roboto,sans-serif;}

  /* ── 页头 ───────────────────────────────────────────── */
  header{background:linear-gradient(115deg,#E4002B 0%,#f2534a 52%,#008C95 100%);color:#fff;}
  .hero{max-width:1120px;margin:0 auto;padding:26px 24px 24px;
    display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:16px;}
  .logo-chip{background:#fff;border-radius:12px;padding:8px 14px;display:flex;align-items:center;
    box-shadow:0 3px 14px rgba(0,0,0,.18);flex:none;}
  .logo{height:34px;width:auto;display:block;}
  .hero-txt h1{margin:0;font-size:22px;line-height:1.35;letter-spacing:.3px;}
  .hero-txt p{margin:5px 0 0;font-size:13.5px;opacity:.93;}
  .back{color:#fff;text-decoration:none;font-size:13px;padding:7px 13px;border-radius:18px;
    background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.34);white-space:nowrap;}
  .back:hover{background:rgba(255,255,255,.26);}
  .back[hidden]{display:none;}

  /* ── 版面 ───────────────────────────────────────────── */
  .wrap{max-width:1120px;margin:0 auto;padding:24px 24px 64px;}

  /* 章节快捷跳转 */
  .snav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 22px;}
  .snav a{font-size:12.5px;color:var(--sub);text-decoration:none;background:var(--card);
    border:1px solid var(--line);border-radius:18px;padding:5px 12px;transition:.15s;}
  .snav a:hover{color:var(--accent);border-color:#f3b8bd;}

  /* 关键数字 */
  .kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:24px;}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:18px 20px;
    box-shadow:0 1px 2px rgba(20,40,80,.04);}
  .kpi .v{font-size:clamp(24px,2.6vw,30px);font-weight:800;color:var(--accent);
    line-height:1.15;letter-spacing:-.4px;font-variant-numeric:tabular-nums;}
  .kpi .v.sm{font-size:clamp(18px,2vw,22px);letter-spacing:0;}
  .kpi .l{font-size:13px;color:var(--sub);margin-top:4px;}

  /* 卡片 */
  section.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
    padding:22px 24px 16px;margin-bottom:22px;box-shadow:0 1px 2px rgba(20,40,80,.04);scroll-margin-top:16px;}
  .card h2{font-size:17.5px;margin:0 0 6px;display:flex;align-items:center;gap:9px;line-height:1.45;}
  .card h2 .no{flex:none;width:24px;height:24px;border-radius:8px;background:var(--accent);color:#fff;
    font-size:12.5px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;
    font-variant-numeric:tabular-nums;}
  .card .desc{color:var(--sub);font-size:13px;margin:0 0 14px;max-width:64em;}
  .card .desc b{color:var(--ink);font-weight:600;}

  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;}

  /* 图表容器：高度由具体 class 决定，手机端统一压缩 */
  .chart{width:100%;height:400px;}
  .chart.h340{height:340px;}
  .chart.h360{height:360px;}
  .chart.h430{height:430px;}
  .chart.h460{height:460px;}
  /* 手机上 X 轴标签挤不下时，给一个可横向滑动的画布 */
  .chart-scroll{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;}
  .chart-scroll>.chart{min-width:620px;}
  .mob-only{display:none;}

  /* 主题切换按钮 */
  .btns{display:flex;flex-wrap:wrap;gap:7px;margin:2px 0 12px;}
  .btn{border:1px solid var(--line);background:var(--soft);color:var(--ink);
    padding:5px 11px;border-radius:18px;font-size:12.5px;cursor:pointer;transition:.15s;white-space:nowrap;}
  .btn:hover{border-color:#f0a9ae;}
  .btn.on{background:var(--accent);color:#fff;border-color:var(--accent);box-shadow:0 1px 6px rgba(228,0,43,.22);}
  .btn .sw{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:1px;}

  select{padding:6px 10px;border:1px solid var(--line);border-radius:9px;font-size:13px;background:#fff;color:var(--ink);}

  /* 结论 */
  .insight{font-size:14px;color:#334149;}
  .insight .lead{font-size:15px;line-height:1.8;margin:0 0 16px;}
  .insight b{color:var(--accent);}
  .facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:0 0 18px;}
  .fact{background:var(--soft);border-radius:12px;padding:13px 15px;border:1px solid #e3ecf3;}
  .fact .n{font-size:21px;font-weight:800;color:var(--accent2);line-height:1.2;font-variant-numeric:tabular-nums;}
  .fact .t{font-size:12.5px;color:var(--sub);margin-top:3px;}
  .insight ul{margin:0 0 14px;padding-left:20px;}
  .insight li{margin-bottom:7px;}
  .insight .note{color:var(--sub);font-size:12.5px;margin:14px 0 0;}

  /* 文章检索 */
  .filters{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:12px;}
  .filters input{padding:7px 11px;border:1px solid var(--line);border-radius:9px;font-size:13px;
    min-width:190px;flex:1 1 190px;max-width:280px;}
  .filters .hint{color:var(--sub);font-size:12.5px;}
  .tblwrap{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:12px;}
  table{width:100%;border-collapse:collapse;font-size:13px;min-width:660px;}
  th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top;}
  th{color:var(--sub);font-weight:600;position:sticky;top:0;background:#fbfcfe;z-index:1;
    font-size:12.5px;letter-spacing:.2px;}
  tbody tr:last-child td{border-bottom:0;}
  tbody tr:hover{background:#fafcff;}
  td.date{white-space:nowrap;color:var(--sub);font-variant-numeric:tabular-nums;width:92px;}
  td.title{line-height:1.55;}
  td.primary{width:96px;}
  .pill{display:inline-block;padding:1px 8px;border-radius:10px;color:#fff;font-size:11.5px;
    white-space:nowrap;line-height:1.7;}
  .taglist{display:flex;flex-wrap:wrap;gap:4px;}

  .err{background:#fff4f4;border:1px solid #ffd3d3;color:#a1121f;padding:14px 16px;border-radius:10px;font-size:13.5px;}
  .foot{color:var(--sub);font-size:12px;text-align:center;line-height:1.9;margin-top:28px;}

  /* ── 手机 ───────────────────────────────────────────── */
  @media(max-width:860px){
    .grid2{grid-template-columns:1fr;gap:14px;}
    .chart{height:320px;}
    /* 环形图和堆叠图的图例要占几行，手机上不再压缩高度，否则图例会压到图里 */
    .chart.h360{height:300px;}
    .chart.h430,.chart.h460{height:340px;}
    .mob-only{display:inline;}
    /* 手机上塞不下四列：去掉「全部标签」，只留日期/标题/主主题，标题就能正常换行 */
    table{min-width:0;}
    #tbl th:nth-child(4),#tbl td:nth-child(4){display:none;}
    td.date{width:82px;}
    td.primary{width:84px;}
  }
  @media(max-width:640px){
    .hero{grid-template-columns:1fr;gap:12px;padding:20px 16px 18px;}
    .logo-chip{padding:6px 11px;width:max-content;}
    .logo{height:28px;}
    .hero-txt h1{font-size:18px;}
    .hero-txt p{font-size:12.5px;line-height:1.6;}
    .back{justify-self:start;font-size:12px;padding:5px 11px;}
    .wrap{padding:16px 14px 48px;}
    section.card{padding:18px 15px 12px;border-radius:14px;margin-bottom:16px;}
    .card h2{font-size:16px;}
    .kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;}
    .kpi{padding:14px 15px;}
    .kpi .v{font-size:22px;}
    .kpi .v.sm{font-size:17px;}
    .card .desc{font-size:12.5px;}
    th,td{padding:8px 10px;font-size:12.5px;}
    .filters input{max-width:none;}
  }
</style>
</head>
<body>
<header>
  <div class="hero">
    <div class="logo-chip">__LOGO__</div>
    <div class="hero-txt">
      <h1>救助儿童会公众号 · 内容分析</h1>
      <p>2014–2026 年全部推文：在写什么、议题怎么变、写法有什么特征</p>
    </div>
    __BACKBAR__
  </div>
</header>

<div class="wrap">
  <nav class="snav" id="snav" aria-label="章节"></nav>
  <div class="kpis" id="kpis"></div>

  <section class="card" id="s1">
    <h2><span class="no">1</span>发文节奏总览</h2>
    <p class="desc">柱＝当年文章数，折线＝当年篇均字符数。<b id="trendNote"></b></p>
    <div id="trend" class="chart"></div>
  </section>

  <section class="card" id="s2">
    <h2><span class="no">2</span>核心：关心的主题</h2>
    <p class="desc">左为各主题文章占比，点扇区可在下方联动「代表关键词」；右为主题随年份的演变。
      全部内容都围绕儿童，这里进一步拆成 14 类（含运营类）。</p>
    <div class="grid2">
      <div id="donut" class="chart h340"></div>
      <div id="stack" class="chart h340"></div>
    </div>
  </section>

  <section class="card" id="s3">
    <h2><span class="no">3</span>各主题代表关键词</h2>
    <p class="desc">按「该词在本主题文章中出现多少篇」排序。点上方按钮或上图扇区切换主题。</p>
    <div class="btns" id="themeBtns"></div>
    <div id="themeWords" class="chart h360"></div>
  </section>

  <section class="card" id="s4">
    <h2><span class="no">4</span>总体高频词与关键词结构</h2>
    <p class="desc">全库分词后的高频实词（左）与词频占比树图（右）。</p>
    <div class="grid2">
      <div id="topwords" class="chart h430"></div>
      <div id="treemap" class="chart h430"></div>
    </div>
  </section>

  <section class="card" id="s5">
    <h2><span class="no">5</span>年度特征词（TF-IDF）</h2>
    <p class="desc">各年份相较全库的特异性用词，反映当年焦点议题。</p>
    <div class="filters"><span class="hint">选择年份</span><select id="yearSel"></select></div>
    <div id="tfidf" class="chart h360"></div>
  </section>

  <section class="card" id="s6">
    <h2><span class="no">6</span>主题共现热力图</h2>
    <p class="desc">同一篇文章同时命中两个主题的篇数。颜色越深，两主题越常结伴出现。<span class="mob-only">图上可左右滑动。</span></p>
    <div class="chart-scroll"><div id="cooc" class="chart h460"></div></div>
  </section>

  <section class="card" id="s7">
    <h2><span class="no">7</span>文章检索</h2>
    <p class="desc" id="tblCount"></p>
    <div class="filters">
      <input id="kw" placeholder="搜索标题…">
      <select id="fTheme"></select>
      <select id="fYear"></select>
      <span class="hint" id="tblHint"></span>
    </div>
    <div class="tblwrap">
      <table id="tbl">
        <colgroup><col style="width:92px"><col><col style="width:96px"><col style="width:300px"></colgroup>
        <thead><tr><th>日期</th><th>标题</th><th>主主题</th><th>全部标签</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <section class="card" id="s8">
    <h2><span class="no">8</span>结论：到底在关心什么</h2>
    <div class="insight" id="insight"></div>
  </section>

  <div class="foot" id="foot"></div>
</div>

<script>window.DATA = __DATA__;</script>
<script>
/* 图表库：先找同目录本地文件（离线可用），失败再逐个试 CDN。
   本地路径从当前网址推出来，所以放在 /yihot/about/dashboard 还是根目录下都能取到。 */
function loadScript(src){return new Promise(function(res,rej){var s=document.createElement('script');
  s.src=src;s.onload=function(){res();};s.onerror=function(){rej();};document.head.appendChild(s);});}
async function ensureEcharts(){
  if(window.echarts) return;
  var local = location.protocol==='file:'
    ? 'echarts.min.js'
    : location.pathname.replace(/\/$/,'') + '/echarts.min.js';
  var cdns=[local,
            'https://cdn.bootcdn.net/ajax/libs/echarts/5.5.1/echarts.min.js',
            'https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js',
            'https://unpkg.com/echarts@5.5.1/dist/echarts.min.js'];
  for(var i=0;i<cdns.length;i++){ try{ await loadScript(cdns[i]); if(window.echarts) return; }catch(e){} }
}
ensureEcharts().then(function(){ init(false); }).catch(function(){ init(true); });

var D = window.DATA;
var MOB = function(){ return window.innerWidth < 640; };
var SECTIONS=[['s1','① 发文节奏'],['s2','② 主题'],['s3','③ 代表词'],['s4','④ 高频词'],
              ['s5','⑤ 年度词'],['s6','⑥ 共现'],['s7','⑦ 检索'],['s8','⑧ 结论']];

function init(failed){
  buildNav();
  if(failed || !window.echarts){
    document.getElementById('trend').innerHTML='<div class="err">图表库加载失败：本地 echarts.min.js 与 CDN 都取不到。文字结论与检索表仍可用。</div>';
    buildStatic(); return;
  }
  buildKPIs();
  chartTrend(); chartDonut(); chartStack(); buildThemeBtns(); chartThemeWords(D.themes[0].key);
  chartTopWords(); chartTreemap(); buildYearSel(); chartTfidf(D.meta.year_max);
  chartCooc(); buildTable(); buildInsight();
  window.addEventListener('resize', function(){
    Object.keys(CHARTS).forEach(function(k){ CHARTS[k] && CHARTS[k].resize(); });
  });
}
var CHARTS={};
function mk(id){ var el=document.getElementById(id); if(!el) return null;
  if(CHARTS[id]) { CHARTS[id].dispose(); }
  var c=echarts.init(el); CHARTS[id]=c; return c; }
var TKEY={}; D.themes.forEach(function(t){TKEY[t.key]=t;});

function buildNav(){
  document.getElementById('snav').innerHTML=SECTIONS.map(function(s){
    return '<a href="#'+s[0]+'">'+s[1]+'</a>';}).join('');
  /* 本地双击打开时没有站点可回，藏掉返回条，免得点了是死链 */
  if(typeof location!=='undefined' && location.protocol==='file:'){ var bk=document.querySelector('.back'); if(bk) bk.hidden=true; }
}

/* 只留 6 个真正有信息量的数字；「2014–2026」用略小的字号，避免换行。 */
function buildKPIs(){
  var m=D.meta;
  var yrs=D.yearly.slice().sort(function(a,b){return b.count-a.count;});
  var peak=yrs[0];
  var totC=D.yearly.reduce(function(s,y){return s+y.total_char;},0);
  var lastYear=m.year_max;
  var items=[
    {v:m.total.toLocaleString(), l:'历史文章（篇）'},
    {v:m.year_min+'–'+m.year_max, l:'覆盖年份', sm:true},
    {v:m.theme_count, l:'主题领域'},
    {v:peak.year, l:'发文峰值年（'+peak.count+' 篇）'},
    {v:Math.round(totC/m.total).toLocaleString(), l:'篇均字符数'},
    {v:m.vocab_size.toLocaleString(), l:'分词词库（去重）'}
  ];
  document.getElementById('kpis').innerHTML=items.map(function(i){
    return '<div class="kpi"><div class="v'+(i.sm?' sm':'')+'">'+i.v+'</div><div class="l">'+i.l+'</div></div>';}).join('');
  var yLast=D.yearly.filter(function(y){return y.year==lastYear;})[0];
  /* 「未完年份」用该年最后一篇文章的日期说，而不是数据生成日期——两者可能差半年。 */
  var lastDates=D.articles.filter(function(a){return String(a.year)===String(lastYear)&&a.date;})
    .map(function(a){return a.date;}).sort();
  var lastDate=lastDates.length?lastDates[lastDates.length-1]:m.generated;
  document.getElementById('trendNote').textContent=(yLast&&yLast.count<60)
    ? '注意：'+lastYear+' 年只统计到 '+lastDate+'，是未完年份，不与整年直接比较。' : '';
}

function chartTrend(){
  var x=D.yearly.map(function(y){return y.year;});
  var c=mk('trend'); if(!c) return;
  /* 轴名并入图例，省掉右上角「字符」两字与图例挤在一起的重叠 */
  c.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
    legend:{data:['文章数（篇）','篇均字符'],top:0,right:0,itemWidth:14,itemHeight:9,textStyle:{fontSize:12}},
    grid:{left:52,right:58,top:42,bottom:34},
    xAxis:{type:'category',data:x,axisLabel:{fontSize:11},axisTick:{show:false}},
    yAxis:[{type:'value',splitLine:{lineStyle:{color:'#f0f3f7'}},axisLabel:{fontSize:11}},
           {type:'value',splitLine:{show:false},axisLabel:{fontSize:11}}],
    series:[
      {name:'文章数（篇）',type:'bar',data:D.yearly.map(function(y){return y.count;}),
       itemStyle:{color:'#E4002B',borderRadius:[4,4,0,0]},barMaxWidth:34},
      {name:'篇均字符',type:'line',yAxisIndex:1,smooth:true,symbol:'circle',symbolSize:6,
       data:D.yearly.map(function(y){return Math.round(y.avg_char);}),
       itemStyle:{color:'#008C95'},lineStyle:{width:2.5}}]
  });
}

/* 环形图：14 个标签放外面容易撞，改成「图内只留百分比，名称交给两行图例」 */
function chartDonut(){
  var mob=MOB();
  var c=mk('donut'); if(!c) return;
  var data=D.themes.map(function(t){return {name:t.label,value:t.count,key:t.key,itemStyle:{color:t.color}};});
  c.setOption({
    tooltip:{trigger:'item',formatter:'{b}：{c} 篇（{d}%）'},
    legend:{type:'plain',bottom:2,left:'center',itemWidth:9,itemHeight:9,itemGap:11,
      textStyle:{fontSize:11.5,color:'#5b6875'},data:D.themes.map(function(t){return t.label;})},
    series:[{type:'pie',radius:mob?['36%','54%']:['42%','62%'],center:['50%',mob?'38%':'42%'],
      avoidLabelOverlap:true,
      label:{show:true,position:'inside',formatter:function(p){return p.percent>=4?p.percent+'%':'';},
        fontSize:11,color:'#fff',fontWeight:600},
      labelLine:{show:false},
      emphasis:{label:{show:true,fontSize:11,formatter:'{b}\n{d}%'}},
      data:data}]
  });
  c.on('click',function(p){ if(p.data&&p.data.key){ chartThemeWords(p.data.key);
    document.querySelectorAll('#themeBtns .btn').forEach(function(b){b.classList.toggle('on',b.dataset.k===p.data.key);}); } });
}

function chartStack(){
  var mob=MOB();
  var c=mk('stack'); if(!c) return;
  var years=D.yearly.map(function(y){return y.year;});
  var series=D.themes.map(function(t){
    return {name:t.label,type:'line',stack:'t',areaStyle:{opacity:.78},
      smooth:true,symbol:'none',emphasis:{focus:'series'},
      lineStyle:{width:0},itemStyle:{color:t.color},
      data:years.map(function(y){return t.by_year[String(y)]||0;})};
  });
  c.setOption({
    tooltip:{trigger:'axis'},
    /* 图例换两行是常态，grid 顶部按行数留白；轴名去掉，避免和最后一行图例贴在一起 */
    legend:{type:'plain',top:0,left:'center',itemWidth:9,itemHeight:9,itemGap:10,
      textStyle:{fontSize:10.5,color:'#5b6875'},data:D.themes.map(function(t){return t.label;})},
    grid:{left:42,right:14,top:mob?104:66,bottom:24},
    xAxis:{type:'category',data:years,boundaryGap:false,axisLabel:{fontSize:11},axisTick:{show:false}},
    yAxis:{type:'value',splitLine:{lineStyle:{color:'#f0f3f7'}},axisLabel:{fontSize:11}},
    series:series
  });
}

function buildThemeBtns(){
  var box=document.getElementById('themeBtns');
  box.innerHTML=D.themes.map(function(t,i){
    return '<span class="btn'+(i===0?' on':'')+'" data-k="'+t.key+'"><span class="sw" style="background:'+t.color+'"></span>'+t.label+' ('+t.count+')</span>';}).join('');
  box.querySelectorAll('.btn').forEach(function(b){
    b.onclick=function(){ chartThemeWords(b.dataset.k);
      box.querySelectorAll('.btn').forEach(function(x){x.classList.remove('on');}); b.classList.add('on'); };
  });
}

/* 说明：data.json 里 top_words.score（主题内/外 lift）每篇都相同，画成条形没有意义，
   所以横轴改用「该主题下出现过此词的文章数」n；按 n 排序取前 12。 */
function chartThemeWords(key){
  var t=TKEY[key]; var c=mk('themeWords'); if(!c||!t) return;
  var words=(t.top_words||[]).slice().sort(function(a,b){return b.n-a.n;}).slice(0,12).slice().reverse();
  c.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      formatter:function(ps){var p=ps[0]; return p.name+'：出现在 '+p.value+' 篇文章';}},
    grid:{left:MOB()?78:96,right:52,top:12,bottom:26},
    xAxis:{type:'value',name:'篇',nameTextStyle:{fontSize:11,color:'#8b98a5'},
      splitLine:{lineStyle:{color:'#f0f3f7'}},axisLabel:{fontSize:11}},
    yAxis:{type:'category',data:words.map(function(w){return w.word;}),
      axisLabel:{fontSize:12},axisTick:{show:false},axisLine:{show:false}},
    series:[{type:'bar',data:words.map(function(w){return w.n;}),
      itemStyle:{color:t.color,borderRadius:[0,4,4,0]},barMaxWidth:18,
      label:{show:true,position:'right',fontSize:11,color:'#6b7885'}}]
  });
}

function chartTopWords(){
  var c=mk('topwords'); if(!c) return;
  var w=D.overall_top_words.slice(0,20).slice().reverse();
  c.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:'{b}：{c} 次'},
    grid:{left:MOB()?66:74,right:64,top:12,bottom:26},
    xAxis:{type:'value',name:'词频',nameTextStyle:{fontSize:11,color:'#8b98a5'},
      splitLine:{lineStyle:{color:'#f0f3f7'}},axisLabel:{fontSize:11}},
    yAxis:{type:'category',data:w.map(function(x){return x.word;}),
      axisLabel:{fontSize:12},axisTick:{show:false},axisLine:{show:false}},
    series:[{type:'bar',data:w.map(function(x){return x.n;}),
      itemStyle:{color:'#008C95',borderRadius:[0,4,4,0]},barMaxWidth:16,
      label:{show:true,position:'right',fontSize:10.5,color:'#6b7885',
        formatter:function(p){return p.value.toLocaleString();}}}]
  });
}

function chartTreemap(){
  var c=mk('treemap'); if(!c) return;
  var d=D.overall_top_words.slice(0,32).map(function(x){return {name:x.word,value:x.n};});
  c.setOption({tooltip:{formatter:'{b}：{c} 次'},
    series:[{type:'treemap',roam:false,nodeClick:false,breadcrumb:{show:false},
      data:d,width:'100%',height:'100%',top:4,bottom:4,left:0,right:0,
      levels:[{itemStyle:{borderColor:'#fff',borderWidth:2,gapWidth:2,borderRadius:4}}],
      label:{show:true,formatter:'{b}',fontSize:12,overflow:'truncate',color:'#fff'}}]});
}

function buildYearSel(){
  var sel=document.getElementById('yearSel');
  sel.innerHTML=D.yearly.map(function(y){return '<option value="'+y.year+'">'+y.year+'</option>';}).join('');
  sel.value=D.meta.year_max;
  sel.onchange=function(){ chartTfidf(parseInt(sel.value,10)); };
}

function chartTfidf(year){
  var c=mk('tfidf'); if(!c) return;
  var arr=(D.tfidf_year[String(year)]||[]).slice(0,12).slice().reverse();
  if(!arr.length){ c.setOption({title:{text:year+' 年特征词不足',left:'center',top:'center',textStyle:{color:'#9aa6b2',fontSize:14,fontWeight:400}}}); return; }
  c.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:'{b}<br/>特异性：{c} 倍'},
    grid:{left:MOB()?78:96,right:58,top:12,bottom:26},
    xAxis:{type:'value',name:'倍',nameTextStyle:{fontSize:11,color:'#8b98a5'},
      splitLine:{lineStyle:{color:'#f0f3f7'}},axisLabel:{fontSize:11}},
    yAxis:{type:'category',data:arr.map(function(x){return x.word;}),
      axisLabel:{fontSize:12},axisTick:{show:false},axisLine:{show:false}},
    series:[{type:'bar',data:arr.map(function(x){return x.score;}),
      itemStyle:{color:'#E4002B',borderRadius:[0,4,4,0]},barMaxWidth:18,
      label:{show:true,position:'right',fontSize:10.5,color:'#6b7885'}}]
  });
}

function chartCooc(){
  var c=mk('cooc'); if(!c) return;
  var keys=D.themes.map(function(t){return t.key;});
  var labels=D.themes.map(function(t){return t.label;});
  var idx={}; keys.forEach(function(k,i){idx[k]=i;});
  var mx=keys.map(function(){return keys.map(function(){return 0;});});
  D.cooccurrence.forEach(function(o){
    if(idx[o.a]!=null&&idx[o.b]!=null){ mx[idx[o.a]][idx[o.b]]+=o.n; mx[idx[o.b]][idx[o.a]]+=o.n; }
  });
  var maxv=0; for(var i=0;i<keys.length;i++)for(var j=0;j<keys.length;j++) if(i!==j) maxv=Math.max(maxv,mx[i][j]);
  var data=[]; for(var i=0;i<keys.length;i++)for(var j=0;j<keys.length;j++) data.push([j,i,mx[i][j]]);
  c.setOption({
    tooltip:{formatter:function(p){return labels[p.value[1]]+' × '+labels[p.value[0]]+'：'+p.value[2]+' 篇';}},
    grid:{left:88,right:18,top:14,bottom:96},
    xAxis:{type:'category',data:labels,position:'bottom',
      axisLabel:{rotate:42,fontSize:11,interval:0,margin:9},axisTick:{show:false}},
    yAxis:{type:'category',data:labels,axisLabel:{fontSize:11},axisTick:{show:false},inverse:true},
    visualMap:{min:0,max:maxv,calculable:true,orient:'horizontal',left:'center',bottom:4,
      itemWidth:11,itemHeight:120,inRange:{color:['#f4f7fa','#a9cdda','#3f9fb3','#02525f']},
      textStyle:{fontSize:10.5,color:'#8b98a5'}},
    series:[{type:'heatmap',data:data,
      itemStyle:{borderColor:'#fff',borderWidth:1.5},
      emphasis:{itemStyle:{shadowBlur:8,shadowColor:'rgba(0,0,0,.28)'}}}]
  });
}

function buildTable(){
  var selT=document.getElementById('fTheme');
  selT.innerHTML='<option value="">全部主题</option>'+D.themes.map(function(t){
    return '<option value="'+t.key+'">'+t.label+'</option>';}).join('');
  var selY=document.getElementById('fYear');
  var years=D.yearly.map(function(y){return y.year;});
  selY.innerHTML='<option value="">全部年份</option>'+years.map(function(y){
    return '<option value="'+y+'">'+y+'</option>';}).join('');
  var kw=document.getElementById('kw');
  [selT,selY,kw].forEach(function(el){el.oninput=renderTable;el.onchange=renderTable;});
  document.getElementById('tblHint').textContent='默认按日期倒序，最多显示 300 条';
  renderTable();
}
function esc(s){return (s||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function renderTable(){
  var kt=document.getElementById('fTheme').value;
  var ky=document.getElementById('fYear').value;
  var kk=document.getElementById('kw').value.trim();
  var rows=D.articles.filter(function(a){
    if(kt&&a.primary!==kt&&a.themes.indexOf(kt)<0) return false;
    if(ky&&String(a.year)!==ky) return false;
    if(kk&&a.title.indexOf(kk)<0) return false;
    return true;
  }).sort(function(a,b){ return (b.date||'').localeCompare(a.date||''); });
  var shown=rows.slice(0,300);
  document.getElementById('tblCount').textContent='共匹配 '+rows.length+' 篇'+(rows.length>300?'，下面显示最近 300 篇':'');
  var tb=document.querySelector('#tbl tbody');
  /* 标签最多显示 3 个，其余折成 +N：原来一行六七枚徽章，整张表变成色块墙。 */
  tb.innerHTML=shown.map(function(a){
    var pc=TKEY[a.primary]?TKEY[a.primary].color:'#9aa6b2';
    var pl=TKEY[a.primary]?TKEY[a.primary].label:a.primary;
    var ks=a.themes.filter(function(k){return TKEY[k]&&k!==a.primary;});
    var shownTags=ks.slice(0,3).map(function(k){var t=TKEY[k];
      return '<span class="pill" style="background:'+t.color+'">'+t.label+'</span>';}).join('');
    var more=ks.length>3?'<span class="pill" style="background:#aab6c2">+'+(ks.length-3)+'</span>':'';
    return '<tr><td class="date">'+esc(a.date||'')+'</td>'
      +'<td class="title">'+esc(a.title)+'</td>'
      +'<td class="primary"><span class="pill" style="background:'+pc+'">'+pl+'</span></td>'
      +'<td><div class="taglist">'+shownTags+more+'</div></td></tr>';
  }).join('');
}

function buildInsight(){
  var m=D.meta;
  var byCount=D.themes.slice().sort(function(a,b){return b.count-a.count;});
  var tot=m.total;
  function pct(k){var t=TKEY[k];return t?Math.round(t.count/tot*1000)/10:0;}
  function cnt(k){var t=TKEY[k];return t?t.count:0;}
  var childKeys=['child_protection','health_nutrition','education','women_girls','parenting',
                 'disability','youth','environment','disaster','digital','fundraising'];
  var childSum=childKeys.reduce(function(s,k){return s+cnt(k);},0);
  var peak=D.yearly.slice().sort(function(a,b){return b.count-a.count;})[0];
  var first=D.yearly[0], last=D.yearly[D.yearly.length-1];

  var html='<p class="lead"><b>一句话：</b>这是一家以儿童为中心的国际组织账号——'+tot+' 篇内容全部围绕儿童福祉，'
    +'可进一步拆成 '+m.theme_count+' 个使命/运营领域；其中教育与招募实习两头最大，中间是保护、健康、性别、环境等议题。</p>';

  html+='<div class="facts">'
    +'<div class="fact"><div class="n">'+Math.round(childSum/tot*100)+'%</div><div class="t">属使命类议题（11 类合计 '+childSum+' 篇）</div></div>'
    +'<div class="fact"><div class="n">'+cnt('education')+' 篇</div><div class="t">儿童教育 '+pct('education')+'%，绝对主力</div></div>'
    +'<div class="fact"><div class="n">'+cnt('recruitment')+' 篇</div><div class="t">招募实习 '+pct('recruitment')+'%，运营类</div></div>'
    +'<div class="fact"><div class="n">'+peak.year+'</div><div class="t">发文峰值年，'+peak.count+' 篇</div></div>'
    +'</div>';

  html+='<ul>'
    +'<li><b>儿童教育</b>：'+cnt('education')+' 篇（'+pct('education')+'%）——学前教育、全纳/融合教育、「玩中学」、亲子阅读。</li>'
    +'<li><b>性别平等</b>：'+cnt('women_girls')+' 篇（'+pct('women_girls')+'%）——母亲/母乳喂养、女童多元发展。</li>'
    +'<li><b>儿童保护</b>：'+cnt('child_protection')+' 篇（'+pct('child_protection')+'%）——防拐卖、强制报告、儿童之家/儿童主任、未成年人司法。</li>'
    +'<li><b>环境保护</b>：'+cnt('environment')+' 篇（'+pct('environment')+'%）——气候变化、生态、气候资金倡导，近年明显上升。</li>'
    +'<li><b>募集筹款</b>：'+cnt('fundraising')+' 篇（'+pct('fundraising')+'%）——捐赠/慈善/公益节，占比小但属品牌与资源端。</li>'
    +'</ul>';

  html+='<p><b>完整主题榜（按体量）：</b>'
    +byCount.map(function(t){return t.label+' '+t.count+'（'+t.pct+'%）';}).join('、')+'。</p>';

  html+='<p><b>节奏：</b>发文从 '+first.year+' 年的 '+first.count+' 篇，涨到 '+peak.year+' 年的 '+peak.count+' 篇峰值；'
    +'近年「环境保护」「网络保护」「残障融合」等新兴议题占比走高，议程随全球议题（气候危机、儿童网络安全）扩展。'
    +'最后一格 '+last.year+' 年只到 '+m.generated+'，是未完年份。</p>';

  html+='<p class="note">注：主题为基于关键词词典的多标签自动归类，单篇可命中多个主题，因此各主题占比相加大于 100%。'
    +'「招募实习」属运营类，不计入使命议题，但占比不小，反映机构常年大量招募。</p>';

  document.getElementById('insight').innerHTML=html;
  document.getElementById('foot').innerHTML='数据来源：救助儿童会微信公众号历史文章（清洗稿 '+tot+' 篇）'
    +' · 分析：Python + jieba 分词 + 关键词主题归类 · 生成于 '+m.generated;
}

function buildStatic(){
  buildKPIs(); buildInsight(); buildTable();
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    args, data_js, logo, backbar = main()
    html = HTML.replace("__DATA__", data_js).replace("__LOGO__", logo).replace("__BACKBAR__", backbar)
    out = args.out
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 写出:", out, round(os.path.getsize(out)/1024,1), "KB", "(site mode)" if args.site else "")
