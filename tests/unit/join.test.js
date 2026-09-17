// Unir lineas (Ctrl+J): softJoins / hardBreak
module.exports = (t, api, h) => {
  const apply = (text, changes) => { let out = text, off = 0; for (const c of changes) { out = out.slice(0, c.from + off) + c.insert + out.slice(c.to + off); off += c.insert.length - (c.to - c.from); } return out; };
  const join = (src) => apply(src, api.softJoins(h.mkDoc(src), { from: 0, to: src.length, text: src }));
  const cases = [
    ['parrafo', 'uno dos\ntres cuatro\ncinco', 'uno dos tres cuatro cinco'],
    ['espacio final simple', 'uno \ndos', 'uno dos'],
    ['salto duro espacios', 'uno  \ndos\ntres', 'uno  \ndos tres'],
    ['salto duro barra', 'uno\\\ndos', 'uno\\\ndos'],
    ['barra escapada no es salto', 'uno\\\\\ndos', 'uno\\\\ dos'],
    ['cita', '> uno\n> dos\n> tres', '> uno dos tres'],
    ['cita perezosa', '> uno\ndos', '> uno dos'],
    ['cita anidada', '> > uno\n> > dos', '> > uno dos'],
    ['item', '- uno\n  dos\n- tres\n  cuatro', '- uno dos\n- tres cuatro'],
    ['item anidado', '- a\n  - b\n    c\n- d', '- a\n  - b c\n- d'],
    ['item numerado', '1. uno\n   dos\n2. tres', '1. uno dos\n2. tres'],
    ['item dentro de cita', '> - uno\n>   dos', '> - uno dos'],
    ['tarea', '- [ ] uno\n  dos', '- [ ] uno dos'],
    ['encabezado no se toca', '# Titulo\nparrafo\nsigue', '# Titulo\nparrafo sigue'],
    ['setext', 'Titulo\n=====', 'Titulo\n====='],
    ['fence', '```\na\nb\n```', '```\na\nb\n```'],
    ['tabla', '| a | b |\n|---|---|\n| 1 | 2 |', '| a | b |\n|---|---|\n| 1 | 2 |'],
    ['lista interrumpe parrafo', 'uno\n- dos', 'uno\n- dos'],
    ['numero distinto de 1 no interrumpe', 'uno\n2. dos', 'uno 2. dos'],
    ['bloque html', '<div>\na\nb\n</div>', '<div>\na\nb\n</div>'],
    ['codigo indentado', '    a\n    b', '    a\n    b'],
    ['una linea', 'solo', 'solo'],
  ];
  for (const [name, src, want] of cases) t.eq(name, join(src), want);
  t.eq('hardBreak: 2 espacios', api.hardBreak('a  '), true);
  t.eq('hardBreak: 1 espacio', api.hardBreak('a '), false);
  t.eq('hardBreak: barra', api.hardBreak('a\\'), true);
  t.eq('hardBreak: barra escapada', api.hardBreak('a\\\\'), false);
  t.eq('hardBreak: tres barras', api.hardBreak('a\\\\\\'), true);
};
