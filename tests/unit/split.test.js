// Unidades de edicion: splitRun (tokens de primer nivel; listas item a item) y blocksOf
module.exports = (t, api, h) => {
  const T = '\t';
  const parts = (text) => api.splitRun(text).map((p) => [p.l0, p.l1, p.li ? p.li.depth : null, p.render]);
  const cases = [
    ['parrafo', 'a\nb', [[0, 1, null, 'a\nb']]],
    ['lista plana', '- a\n- b\n- c', [[0, 0, 0, '- a'], [1, 1, 0, '- b'], [2, 2, 0, '- c']]],
    ['continuacion', '- a\n  sigue\n- b', [[0, 1, 0, '- a\n  sigue'], [2, 2, 0, '- b']]],
    ['anidada 2 espacios', '- a\n  - b\n  - c\n- d', [[0, 0, 0, '- a'], [1, 1, 1, '- b'], [2, 2, 1, '- c'], [3, 3, 0, '- d']]],
    ['anidada 4 espacios (dedentado: no es codigo)', '- a\n    - b\n        - c\n- d', [[0, 0, 0, '- a'], [1, 1, 1, '- b'], [2, 2, 2, '- c'], [3, 3, 0, '- d']]],
    ['anidada con tabulador', '- a\n' + T + '- b\n- c', [[0, 0, 0, '- a'], [1, 1, 1, '- b'], [2, 2, 0, '- c']]],
    ['numerada', '1. a\n2. b\n3. c', [[0, 0, 0, '1. a'], [1, 1, 0, '2. b'], [2, 2, 0, '3. c']]],
    ['numerada con vineta dentro', '1. a\n   - b\n2. c', [[0, 0, 0, '1. a'], [1, 1, 1, '- b'], [2, 2, 0, '2. c']]],
    ['tareas', '- [ ] a\n- [x] b', [[0, 0, 0, '- [ ] a'], [1, 1, 0, '- [x] b']]],
    ['parrafo pegado a lista', 'Intro:\n- a\n- b', [[0, 0, null, 'Intro:'], [1, 1, 0, '- a'], [2, 2, 0, '- b']]],
    ['titulo pegado a parrafo', '## T\ntexto\nmas', [[0, 0, null, '## T'], [1, 2, null, 'texto\nmas']]],
    ['lista + continuacion perezosa', '- a\nlazy', [[0, 1, 0, '- a\nlazy']]],
    ['lista + titulo', '- a\n# T', [[0, 0, 0, '- a'], [1, 1, null, '# T']]],
    ['dos listas (marcador distinto)', '- a\n* b', [[0, 0, 0, '- a'], [1, 1, 0, '* b']]],
    ['cita con lista: una unidad', '> - a\n> - b', [[0, 1, null, '> - a\n> - b']]],
    ['tabla', '| a |\n|---|\n| 1 |', [[0, 2, null, '| a |\n|---|\n| 1 |']]],
    ['fence', '```\n- a\n```', [[0, 2, null, '```\n- a\n```']]],
    ['referencia delante', '[x]: http://e\ntexto', [[0, 1, null, '[x]: http://e\ntexto']]],
    ['referencia detras', 'texto\n[x]: http://e', [[0, 1, null, 'texto\n[x]: http://e']]],
    ['solo referencia', '[x]: http://e', [[0, 0, null, '[x]: http://e']]],
    ['html', '<div>\n- a\n</div>', [[0, 2, null, '<div>\n- a\n</div>']]],
    ['setext', 'T\n===\ntexto', [[0, 1, null, 'T\n==='], [2, 2, null, 'texto']]],
    ['hr', 'a\n***\nb', [[0, 0, null, 'a'], [1, 1, null, '***'], [2, 2, null, 'b']]],
    ['item que empieza por item', '- - a\n- b', [[0, 0, 0, '- - a'], [1, 1, 0, '- b']]],
    ['numerado con item en la misma linea', '1. - a\n   - b\n2. c', [[0, 0, 0, '1. - a'], [1, 1, 1, '- b'], [2, 2, 0, '2. c']]],
  ];
  for (const [name, text, want] of cases) t.eq(name, parts(text), want);
  t.eq('first/last de toda la lista', api.splitRun('- a\n  - b\n- c').map((p) => [p.li.first, p.li.last]), [[true, false], [false, false], [false, true]]);
  t.ok('ol start al renderizar un item suelto', h.md.render('2. b').includes('start="2"'));

  // blocksOf: unidades con posiciones absolutas sobre un doc con varias tiradas
  const src = '# T\n\nuno\ndos\n\n- a\n  - b\n- c\n\n| x |\n|---|\n| 1 |\n';
  const doc = h.mkDoc(src), blocks = api.blocksOf({ doc });
  t.eq('blocksOf: textos', blocks.map((b) => src.slice(b.from, b.to)), ['# T', 'uno\ndos', '- a', '  - b', '- c', '| x |\n|---|\n| 1 |']);
  t.eq('blocksOf: render dedentado del anidado', blocks[3].render, '- b');
  t.eq('blocksOf: li', blocks.slice(2, 5).map((b) => [b.li.depth, b.li.first, b.li.last]), [[0, true, false], [1, false, false], [0, false, true]]);
  t.eq('blockEnd absorbe las lineas en blanco', api.blockEnd(doc, blocks, 1), doc.line(5).to);
  t.eq('blockEnd entre items pegados = fin del item', api.blockEnd(doc, blocks, 2), blocks[2].to);
};
