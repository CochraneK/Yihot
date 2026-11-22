// 无头冒烟测试：stub 浏览器/DOM/echarts，真实执行 index.html 内的脚本逻辑
// 用法：node selftest.js [index.html 路径]
//   默认读同目录 dashboard-output/index.html（先跑 build_dashboard.py 生成）
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = process.argv[2] || path.join(here, 'dashboard-output', 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// 提取所有 <script> 内容
const blocks = [];
const re = /<script[^>]*>([\s\S]*?)<\/script>/g;
let m;
while ((m = re.exec(html)) !== null) blocks.push(m[1]);
console.log('script blocks:', blocks.length);

// 语法检查
blocks.forEach((code, i) => {
  try { new Function(code); }
  catch (e) { console.error('SYNTAX ERROR in block', i, '->', e.message); process.exit(1); }
});
console.log('syntax OK');

// 构造 stub DOM / echarts
function makeEl() {
  const el = {
    _html: '', textContent: '', value: '', dataset: {}, style: {},
    classList: { add(){}, remove(){}, toggle(){} },
    set innerHTML(v){ this._html = v; }, get innerHTML(){ return this._html; },
    querySelector(){ return makeEl(); },
    querySelectorAll(){ const a=[]; a.forEach=Array.prototype.forEach; return a; },
    appendChild(){}, addEventListener(){},
    set oninput(v){}, set onchange(v){}, set onclick(v){}
  };
  return el;
}
const elements = {};
const document = {
  getElementById(id){ return elements[id] || (elements[id] = makeEl()); },
  querySelector(){ return makeEl(); },
  querySelectorAll(){ const a=[]; a.forEach=Array.prototype.forEach; return a; },
  createElement(){ return makeEl(); },
  head: { appendChild(){} },
  addEventListener(){}
};
const echarts = { init(){ return { setOption(){}, on(){}, resize(){} }; } };
const window = { addEventListener(){}, DATA: null };
const location = { protocol: 'file:', pathname: '/about/dashboard/' };

const sandbox = {
  document, echarts, window, location, console,
  setTimeout, clearTimeout, Promise, Math, JSON, Object, Array, String, Number, parseInt, parseFloat
};
sandbox.global = sandbox;

// 执行脚本（先 DATA，再主逻辑）
vm.createContext(sandbox);
try {
  blocks.forEach((code) => { vm.runInContext(code, sandbox, { filename: 'block.js' }); });
} catch (e) {
  console.error('RUNTIME ERROR:', e.message); console.error(e.stack.split('\n').slice(0,4).join('\n'));
  process.exit(1);
}
console.log('scripts executed (init scheduled via ensureEcharts promise)');
console.log('DATA parsed?', !!sandbox.window.DATA,
            'themes=', sandbox.window.DATA ? sandbox.window.DATA.themes.length : 0,
            'articles=', sandbox.window.DATA ? sandbox.window.DATA.articles.length : 0);
// 手动触发 init（绕过异步 loader），验证核心逻辑不抛错
try {
  sandbox.window.echarts = echarts;
  vm.runInContext('if(typeof init==="function"){ init(false); }', sandbox);
  console.log('init() ran without throwing');
  console.log('KPI chips html len:', (elements['chips'] && elements['chips']._html.length) || 0);
  console.log('insight html len:', (elements['insight'] && elements['insight']._html.length) || 0);
  console.log('kpis html len:', (elements['kpis'] && elements['kpis']._html.length) || 0);
} catch (e) {
  console.error('INIT RUNTIME ERROR:', e.message); console.error(e.stack.split('\n').slice(0,5).join('\n'));
  process.exit(1);
}
console.log('SMOKE TEST PASSED');
