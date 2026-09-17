// Operaciones de tabla: parseTable / formatTable (re-alineado de anchos) y TABLE_OPS via tableOp
module.exports = (t, api, h) => {
  const T = [
    '| Épica | Prio | Estado |',
    '|-------|:----:|-------:|',
    '| **Login** | alta | en curso |',
    '| Pagos | media | |',
    '| Corta |',
    '| Con `a\\|b` | baja | hecho |',
  ].join('\n');
  const F = [
    '| Épica      | Prio  |   Estado |',
    '| ---------- | :---: | -------: |',
    '| **Login**  | alta  | en curso |',
    '| Pagos      | media |          |',
    '| Corta      |       |          |',
    '| Con `a\\|b` | baja  |    hecho |',
  ].join('\n');
  const tb = api.parseTable(T);
  t.eq('parseTable: cabecera', tb.rows[0], ['Épica', 'Prio', 'Estado']);
  t.eq('parseTable: alineacion (sin dos puntos = null)', tb.align, [null, 'c', 'r']);
  t.eq('parseTable: fila corta tal cual', tb.rows[3], ['Corta']);
  t.eq('parseTable: pipe escapado se conserva', tb.rows[4][0], 'Con `a\\|b`');
  t.eq('parseTable: :--- = izquierda explicita', api.parseTable('| a | b |\n|:--|---|\n| 1 | 2 |').align, ['l', null]);
  t.eq('formatTable: anchos, relleno segun alineacion y filas cortas completas', api.formatTable(tb), F);
  t.eq('formatTable: idempotente', api.formatTable(api.parseTable(F)), F);
  t.eq('formatTable: minimo 3 (el de ---)', api.formatTable(api.parseTable('|a|b|\n|-|-|\n|1|2|')), '| a   | b   |\n| --- | --- |\n| 1   | 2   |');
  t.eq('formatTable: celdas de mas se conservan al final', api.formatTable(api.parseTable('| a |\n|---|\n| 1 | extra |')), '| a   |\n| --- |\n| 1   | extra |');
  t.eq('strWidth: ideogramas y emoji cuentan doble', [api.strWidth('abc'), api.strWidth('日本'), api.strWidth('a😀')], [3, 4, 3]);
  t.eq('formatTable: alinea con anchos dobles', api.formatTable(api.parseTable('| a | b |\n|---|---|\n| 日本 | 2 |')).split('\n')[2], '| 日本 | 2   |');
  const op = (text, o, r, c) => api.tableOp(text, o, r, c);
  const rows = (res) => res && res.text.split('\n').map((l) => api.tableCells(l).map((s) => l.slice(s.cFrom, s.cTo)));
  // filas
  t.eq('rowAbove en la cabecera: no procede', op(T, 'rowAbove', 0, 0), null);
  let r = op(T, 'rowAbove', 1, 2);
  t.eq('rowAbove: fila vacia encima y se sigue en la misma celda', [rows(r)[2], r.r, r.c], [['', '', ''], 1, 2]);
  r = op(T, 'rowBelow', 0, 1);
  t.eq('rowBelow desde la cabecera: primera fila del cuerpo', [rows(r)[2], rows(r)[3][0], r.r, r.c], [['', '', ''], '**Login**', 1, 1]);
  t.eq('rowBelow al final', rows(op(T, 'rowBelow', 4, 0)).length, 7);
  t.eq('fila o columna fuera de la tabla: null', [op(T, 'rowBelow', 5, 0), op(T, 'rowBelow', 1, 3)], [null, null]);
  t.eq('rowUp de la primera fila del cuerpo: no procede', op(T, 'rowUp', 1, 0), null);
  r = op(T, 'rowUp', 2, 0);
  t.eq('rowUp intercambia con la de encima', [rows(r)[2][0], rows(r)[3][0], r.r], ['Pagos', '**Login**', 1]);
  t.eq('rowDown de la ultima: no procede', op(T, 'rowDown', 4, 0), null);
  t.eq('rowDown de la cabecera: no procede', op(T, 'rowDown', 0, 0), null);
  r = op(T, 'rowDown', 2, 1);
  t.eq('rowDown intercambia con la de debajo', [rows(r)[3][0], rows(r)[4][0], r.r], ['Corta', 'Pagos', 3]);
  t.eq('rowDelete de la cabecera: no procede', op(T, 'rowDelete', 0, 0), null);
  r = op(T, 'rowDelete', 4, 1);
  t.eq('rowDelete de la ultima: se sigue en la nueva ultima', [rows(r).length, r.r], [5, 3]);
  t.eq('rowDelete de la unica fila del cuerpo deja solo la cabecera', op('| a |\n|---|\n| 1 |', 'rowDelete', 1, 0).text, '| a   |\n| --- |');
  // columnas
  r = op(T, 'colLeft', 1, 0);
  t.eq('colLeft: columna vacia en todas las filas y alineacion null', [rows(r)[0], rows(r)[4], api.parseTable(r.text).align, r.c], [['', 'Épica', 'Prio', 'Estado'], ['', 'Corta', '', ''], [null, null, 'c', 'r'], 0]);
  r = op(T, 'colRight', 2, 1);
  t.eq('colRight: se sigue en la columna nueva', [rows(r)[0], api.parseTable(r.text).align, r.c], [['Épica', 'Prio', '', 'Estado'], [null, 'c', null, 'r'], 2]);
  t.eq('colRight tras la ultima', rows(op(T, 'colRight', 1, 2))[2], ['**Login**', 'alta', 'en curso', '']);
  t.eq('colPrev de la primera: no procede', op(T, 'colPrev', 1, 0), null);
  r = op(T, 'colPrev', 1, 2);
  t.eq('colPrev: intercambia celdas y alineacion, tambien en filas cortas', [rows(r)[0], rows(r)[4], api.parseTable(r.text).align, r.c], [['Épica', 'Estado', 'Prio'], ['Corta', '', ''], [null, 'r', 'c'], 1]);
  t.eq('colNext de la ultima: no procede', op(T, 'colNext', 1, 2), null);
  r = op(T, 'colNext', 3, 0);
  t.eq('colNext: intercambia', [rows(r)[0], rows(r)[4], r.c], [['Prio', 'Épica', 'Estado'], ['', 'Corta', ''], 1]);
  t.eq('colDelete de la unica columna: no procede', op('| a |\n|---|\n| 1 |', 'colDelete', 1, 0), null);
  r = op(T, 'colDelete', 1, 2);
  t.eq('colDelete de la ultima: se sigue en la nueva ultima', [rows(r)[0], api.parseTable(r.text).align, r.c], [['Épica', 'Prio'], [null, 'c'], 1]);
  r = op(T, 'colDelete', 1, 0);
  t.eq('colDelete de la primera: la fila corta queda vacia', [rows(r)[0], rows(r)[4]], [['Prio', 'Estado'], ['', '']]);
  // alineacion y anchos
  t.eq('alignCenter escribe :---:', op(T, 'alignCenter', 1, 0).text.split('\n')[1], '| :--------: | :---: | -------: |');
  t.eq('alignRight', api.parseTable(op(T, 'alignRight', 1, 1).text).align, [null, 'r', 'r']);
  t.eq('alignLeft explicito', op(T, 'alignLeft', 1, 2).text.split('\n')[1], '| ---------- | :---: | :------- |');
  t.eq('format: solo re-alinea y devuelve la misma celda', op(T, 'format', 3, 1), { text: F, r: 3, c: 1 });
  t.eq('operacion desconocida: null', op(T, 'nada', 0, 0), null);
};
