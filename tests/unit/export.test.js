// Exportar a texto: exportText(src, 'jira' | 'confluence' | 'slack' | 'teams') sobre los tokens de markdown-it
module.exports = (t, api, h) => {
  const SRC = [
    '# Título *uno*',
    '',
    'Párrafo con **negrita**, _cursiva_, ~~tachado~~, `código` y un [enlace](https://x.org/a) más https://auto.link.',
    'Segunda línea blanda.',
    'Con salto duro  ',
    'tras dos espacios.',
    '',
    '## Lista',
    '',
    '- uno',
    '- dos **fuerte**',
    '  - dos.a',
    '  - dos.b',
    '    1. tres.1',
    '    2. tres.2',
    '',
    '* [ ] tarea pendiente',
    '* [x] tarea hecha',
    '',
    '1. primero',
    '2. segundo',
    '',
    '> cita con `code`',
    '> y otra línea',
    '',
    '```js',
    'const a = 1; // <b> & "c"',
    '```',
    '',
    '| Col | Der | Cen |',
    '|-----|----:|:---:|',
    '| a | 1 | x |',
    '| b `c\\|d` | 22 | |',
    '',
    '![Logo](img/logo.png) y ![Web](https://h.org/i.png)',
    '',
    '---',
    '',
    '<div class="raw">html crudo</div>',
  ].join('\n');
  const jira = api.exportText(SRC, 'jira');
  t.eq('jira: documento completo', jira, [
    'h1. Título _uno_',
    '',
    'Párrafo con *negrita*, _cursiva_, -tachado-, {{código}} y un [enlace|https://x.org/a] más [https://auto.link]. Segunda línea blanda. Con salto duro\\\\',
    'tras dos espacios.',
    '',
    'h2. Lista',
    '',
    '* uno',
    '* dos *fuerte*',
    '** dos.a',
    '** dos.b',
    '**# tres.1',
    '**# tres.2',
    '',
    '* (x) tarea pendiente',
    '* (/) tarea hecha',
    '',
    '# primero',
    '# segundo',
    '',
    '{quote}',
    'cita con {{code}} y otra línea',
    '{quote}',
    '',
    '{code:js}',
    'const a = 1; // <b> & "c"',
    '{code}',
    '',
    '||Col||Der||Cen||',
    '|a|1|x|',
    '|b {{c¦d}}|22| |',
    '',
    '!img/logo.png|alt=Logo! y !https://h.org/i.png|alt=Web!',
    '',
    '----',
    '',
    '<div class="raw">html crudo</div>',
  ].join('\n'));
  t.eq('jira: escapa llaves y corchetes del texto', api.exportText('a {b} [c]', 'jira'), 'a \\{b} \\[c]');
  t.eq('jira: lista numerada con sublista de viñetas', api.exportText('1. a\n   - b\n2. c', 'jira'), '# a\n#* b\n# c');
  t.eq('jira: item con dos párrafos', api.exportText('- a\n\n  b\n- c', 'jira'), '* a\nb\n* c');

  const conf = api.exportText(SRC, 'confluence');
  const has = (name, frag) => t.ok(name, conf.includes(frag), 'falta: ' + frag + '\nen:\n' + conf);
  has('confluence: título con énfasis', '<h1>Título <em>uno</em></h1>');
  has('confluence: inline', '<p>Párrafo con <strong>negrita</strong>, <em>cursiva</em>, <span style="text-decoration: line-through;">tachado</span>, <code>código</code> y un <a href="https://x.org/a">enlace</a> más <a href="https://auto.link">https://auto.link</a>. Segunda línea blanda. Con salto duro<br />tras dos espacios.</p>');
  has('confluence: listas anidadas', '<ul><li>uno</li><li>dos <strong>fuerte</strong><ul><li>dos.a</li><li>dos.b<ol><li>tres.1</li><li>tres.2</li></ol></li></ul></li></ul>');
  has('confluence: lista de tareas', '<ac:task-list><ac:task><ac:task-status>incomplete</ac:task-status><ac:task-body>tarea pendiente</ac:task-body></ac:task><ac:task><ac:task-status>complete</ac:task-status><ac:task-body>tarea hecha</ac:task-body></ac:task></ac:task-list>');
  has('confluence: numerada', '<ol><li>primero</li><li>segundo</li></ol>');
  has('confluence: cita', '<blockquote><p>cita con <code>code</code> y otra línea</p></blockquote>');
  has('confluence: macro de código con lenguaje mapeado y CDATA sin escapar', '<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">javascript</ac:parameter><ac:plain-text-body><![CDATA[const a = 1; // <b> & "c"]]></ac:plain-text-body></ac:structured-macro>');
  has('confluence: tabla con alineación', '<table><tbody><tr><th>Col</th><th style="text-align: right;">Der</th><th style="text-align: center;">Cen</th></tr><tr><td>a</td><td style="text-align: right;">1</td><td style="text-align: center;">x</td></tr><tr><td>b <code>c|d</code></td><td style="text-align: right;">22</td><td style="text-align: center;"></td></tr></tbody></table>');
  has('confluence: imagen local = adjunto por nombre', '<ac:image ac:alt="Logo"><ri:attachment ri:filename="logo.png" /></ac:image>');
  has('confluence: imagen remota = url', '<ac:image ac:alt="Web"><ri:url ri:value="https://h.org/i.png" /></ac:image>');
  has('confluence: regla y html crudo', '<hr />\n<div class="raw">html crudo</div>');
  t.eq('confluence: escapa el texto (el tipógrafo riza las comillas)', api.exportText('a < b & "c"', 'confluence'), '<p>a &lt; b &amp; “c”</p>');
  t.eq('confluence: ]]> dentro del código se parte', api.exportText('```\nx]]>y\n```', 'confluence'), '<ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA[x]]]]><![CDATA[>y]]></ac:plain-text-body></ac:structured-macro>');
  t.eq('confluence: tareas mezcladas con items normales', api.exportText('- a\n- [x] b', 'confluence'), '<ul><li>a</li><li>☑ b</li></ul>');

  const slack = api.exportText(SRC, 'slack');
  const hs = (name, frag) => t.ok(name, slack.includes(frag), 'falta: ' + frag + '\nen:\n' + slack);
  hs('slack: título = negrita', '*Título _uno_*');
  hs('slack: inline', 'Párrafo con *negrita*, _cursiva_, ~tachado~, `código` y un <https://x.org/a|enlace> más <https://auto.link>. Segunda línea blanda. Con salto duro\ntras dos espacios.');
  hs('slack: listas con sangría', '• uno\n• dos *fuerte*\n    • dos.a\n    • dos.b\n        1. tres.1\n        2. tres.2');
  hs('slack: tareas con casilla', '• ☐ tarea pendiente\n• ☑ tarea hecha');
  hs('slack: numerada', '1. primero\n2. segundo');
  hs('slack: cita', '> cita con `code` y otra línea');
  hs('slack: código sin lenguaje', '```\nconst a = 1; // <b> & "c"\n```');
  hs('slack: tabla monoespaciada', '```\nCol      Der  Cen\n-------  ---  ---\na          1   x\nb `c|d`   22\n```');
  hs('slack: imágenes', '[Logo] y <https://h.org/i.png|Web>');
  t.ok('slack: sin html crudo', !slack.includes('html crudo'));

  const teams = api.exportText(SRC, 'teams');
  const ht = (name, frag) => t.ok(name, teams.includes(frag), 'falta: ' + frag + '\nen:\n' + teams);
  ht('teams: título = negrita', '**Título _uno_**');
  ht('teams: inline', 'Párrafo con **negrita**, _cursiva_, ~~tachado~~, `código` y un enlace (https://x.org/a) más https://auto.link.');
  ht('teams: listas con guion y sangría de 2', '- uno\n- dos **fuerte**\n  - dos.a\n  - dos.b\n    1. tres.1\n    2. tres.2');
  ht('teams: tareas', '- ☐ tarea pendiente\n- ☑ tarea hecha');
  ht('teams: código con lenguaje', '```js\nconst a = 1; // <b> & "c"\n```');
  ht('teams: imágenes', '[Logo] y Web (https://h.org/i.png)');

  t.eq('vacío', api.exportText('', 'jira'), '');
  t.eq('numeración con inicio', api.exportText('3. a\n4. b', 'slack'), '3. a\n4. b');
  let err = null; try { api.exportText('x', 'word'); } catch (e) { err = e; }
  t.ok('destino desconocido lanza', !!err);
};
