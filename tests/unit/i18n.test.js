// Traducciones: todas las claves de la UI (marcado [data-i18n], atributos title/aria-label/placeholder,
// T('...') del script y T("...") de mdlive.py) estan en cada i18n/<lang>.json, sin claves huerfanas, y
// las traducciones conservan los {marcadores} y las etiquetas <kbd>/<code>.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

function collectKeys() {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const py = fs.readFileSync(path.join(ROOT, 'mdlive.py'), 'utf8');
  const cut = html.indexOf('<script>\n(function () {');
  const staticHtml = html.slice(0, cut), js = html.slice(cut);
  const norm = (s) => s.trim().replace(/\s+/g, ' ');
  const keys = new Map();   // clave -> origen
  for (const m of staticHtml.matchAll(/<(\w+)(?:\s[^>]*)?\sdata-i18n(?:\s[^>]*)?>([\s\S]*?)<\/\1>/g)) keys.set(norm(m[2]), 'data-i18n');
  for (const m of staticHtml.matchAll(/\s(?:title|aria-label|placeholder)="([^"]+)"/g)) keys.set(m[1], 'atributo');
  for (const m of js.matchAll(/\bT\('((?:[^'\\]|\\.)*)'\s*[,)]/g)) keys.set(m[1].replace(/\\'/g, "'"), 'T() js');
  for (const m of py.matchAll(/\bT\("((?:[^"\\]|\\.)*)"/g)) keys.set(m[1], 'T() py');
  return keys;
}
const marks = (s) => (s.match(/\{\w+\}/g) || []).sort().join(' ');
const tags = (s) => (s.match(/<\/?(?:kbd|code|b|i)>/g) || []).length;

module.exports = function (t, api, h) {
  const keys = collectKeys();
  t.ok('hay claves de UI que traducir (> 120)', keys.size > 120);
  const files = fs.readdirSync(path.join(ROOT, 'i18n')).filter((f) => f.endsWith('.json')).sort();
  t.ok('hay diccionarios (en, de, fr, it, pt)', ['de', 'en', 'fr', 'it', 'pt'].every((l) => files.includes(l + '.json')));
  for (const f of files) {
    const lang = f.replace('.json', '');
    let dict; try { dict = JSON.parse(fs.readFileSync(path.join(ROOT, 'i18n', f), 'utf8')); } catch (e) { t.ok(lang + ': JSON válido', false); continue; }
    const missing = [...keys.keys()].filter((k) => !(k in dict));
    const orphan = Object.keys(dict).filter((k) => !keys.has(k));
    t.eq(lang + ': sin claves que falten', missing, []);
    t.eq(lang + ': sin claves huérfanas', orphan, []);
    const bad = Object.entries(dict).filter(([k, v]) => typeof v !== 'string' || !v.trim() || marks(k) !== marks(v) || tags(k) !== tags(v)).map(([k]) => k);
    t.eq(lang + ': valores no vacíos que conservan {marcadores} y etiquetas', bad, []);
    const same = Object.entries(dict).filter(([k, v]) => k === v && /[a-záéíóúñ]{3,} [a-záéíóúñ]{2,}/.test(k.replace(/<[^>]+>/g, ''))).map(([k]) => k);
    t.ok(lang + ': las frases están traducidas (≤ 3 idénticas al español)', same.length <= 3, same.join(' | '));
  }
};
module.exports.collectKeys = collectKeys;
