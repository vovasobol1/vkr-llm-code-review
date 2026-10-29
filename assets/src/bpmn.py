"""Диаграммы BPMN AS-IS и TO-BE для ЛР 3: SVG по координатам, PNG через headless Chrome.

Запуск из корня репозитория: python3 assets/src/bpmn.py
"""
import os
import subprocess
from html import escape

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

TASK_W, TASK_H = 160, 66
EV_R = 18
GW_R = 26
FONT = 'Arial, Helvetica, sans-serif'

STYLES = {
    None: ('#ffffff', '#333333', ''),
    'bad': ('#fdecea', '#c0392b', '6 4'),
    'new': ('#e8f6ec', '#1e8449', ''),
}


class Diagram:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.el = {}
        self.back = []
        self.front = []

    # ---------- фигуры ----------
    def pool(self, x, y, w, name, lanes):
        self.back.append(f'<rect x="{x}" y="{y}" width="{w}" height="{sum(h for _, h in lanes)}" fill="#fff" stroke="#333" stroke-width="1.5"/>')
        total = sum(h for _, h in lanes)
        self.back.append(f'<line x1="{x + 32}" y1="{y}" x2="{x + 32}" y2="{y + total}" stroke="#333" stroke-width="1.5"/>')
        self.back.append(self._vtext(x + 16, y + total / 2, name, bold=True))
        ly = y
        for i, (lname, lh) in enumerate(lanes):
            if i:
                self.back.append(f'<line x1="{x + 32}" y1="{ly}" x2="{x + w}" y2="{ly}" stroke="#333" stroke-width="1"/>')
            self.back.append(f'<line x1="{x + 64}" y1="{ly}" x2="{x + 64}" y2="{ly + lh}" stroke="#333" stroke-width="1"/>')
            self.back.append(self._vtext(x + 48, ly + lh / 2, lname))
            ly += lh

    def task(self, key, cx, cy, text, style=None, multi=False):
        fill, stroke, dash = STYLES[style]
        x, y = cx - TASK_W / 2, cy - TASK_H / 2
        s = f'<rect x="{x}" y="{y}" width="{TASK_W}" height="{TASK_H}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-dasharray="{dash}"/>'
        s += self._text(cx, cy - (5 if multi else 0), text)
        if multi:
            for dx in (-6, 0, 6):
                s += f'<line x1="{cx + dx}" y1="{y + TASK_H - 16}" x2="{cx + dx}" y2="{y + TASK_H - 4}" stroke="{stroke}" stroke-width="2"/>'
        self.front.append(s)
        self.el[key] = ('box', cx, cy, TASK_W / 2, TASK_H / 2)

    def start(self, key, cx, cy, label):
        self._event(key, cx, cy, label, 1.5)

    def end(self, key, cx, cy, label):
        self._event(key, cx, cy, label, 4)

    def _event(self, key, cx, cy, label, sw):
        s = f'<circle cx="{cx}" cy="{cy}" r="{EV_R}" fill="#fff" stroke="#333" stroke-width="{sw}"/>'
        s += self._text(cx, cy + EV_R + 18, label, size=12)
        self.front.append(s)
        self.el[key] = ('box', cx, cy, EV_R, EV_R)

    def subprocess(self, key, x, y, w, h, title, style=None):
        fill, stroke, dash = STYLES[style]
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" fill-opacity="0.45" stroke="{stroke}" stroke-width="2" stroke-dasharray="{dash}"/>'
        s += f'<text x="{x + 12}" y="{y + 20}" font-family="{FONT}" font-size="13" font-weight="bold" fill="#222">{escape(title)}</text>'
        cx = x + w / 2
        for dx in (-6, 0, 6):
            s += f'<line x1="{cx + dx}" y1="{y + h - 18}" x2="{cx + dx}" y2="{y + h - 5}" stroke="{stroke}" stroke-width="2"/>'
        self.back.append(s)
        self.el[key] = ('box', x + w / 2, y + h / 2, w / 2, h / 2)

    def error_boundary(self, key, cx, cy, label):
        s = f'<circle cx="{cx}" cy="{cy}" r="{EV_R}" fill="#fff" stroke="#333" stroke-width="1.5"/>'
        s += f'<circle cx="{cx}" cy="{cy}" r="{EV_R - 4}" fill="none" stroke="#333" stroke-width="1.2"/>'
        s += f'<path d="M{cx - 7} {cy + 7} L{cx - 3} {cy - 6} L{cx + 2} {cy + 2} L{cx + 7} {cy - 7}" fill="none" stroke="#333" stroke-width="2"/>'
        s += f'<text x="{cx + EV_R + 6}" y="{cy + 22}" font-family="{FONT}" font-size="12" fill="#222">{escape(label)}</text>'
        self.front.append(s)
        self.el[key] = ('box', cx, cy, EV_R, EV_R)

    def error_end(self, key, cx, cy, label):
        s = f'<circle cx="{cx}" cy="{cy}" r="{EV_R}" fill="#fff" stroke="#333" stroke-width="4"/>'
        s += f'<path d="M{cx - 7} {cy + 7} L{cx - 3} {cy - 6} L{cx + 2} {cy + 2} L{cx + 7} {cy - 7}" fill="none" stroke="#333" stroke-width="2"/>'
        s += f'<text x="{cx + EV_R + 6}" y="{cy + 4}" font-family="{FONT}" font-size="12" fill="#222">{escape(label)}</text>'
        self.front.append(s)
        self.el[key] = ('box', cx, cy, EV_R, EV_R)

    def gateway(self, key, cx, cy, label, label_pos='top', dx=0, kind='x'):
        r = GW_R
        s = f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}" fill="#fff" stroke="#333" stroke-width="1.5"/>'
        d = 8
        if kind == 'x':
            s += f'<path d="M{cx - d} {cy - d} L{cx + d} {cy + d} M{cx + d} {cy - d} L{cx - d} {cy + d}" stroke="#333" stroke-width="2.5"/>'
        else:
            s += f'<circle cx="{cx}" cy="{cy}" r="{r / 2.3}" fill="none" stroke="#333" stroke-width="2.5"/>'
        if label:
            n = label.count('\n')
            ty = cy - r - 10 - 14 * n if label_pos == 'top' else cy + r + 18
            s += self._text(cx + dx, ty, label, size=12, valign='top')
        self.front.append(s)
        self.el[key] = ('box', cx, cy, r, r)

    def store(self, key, cx, cy, label, right=False):
        w, h, e = 56, 46, 9
        x, y = cx - w / 2, cy - h / 2
        s = (f'<path d="M{x} {y + e} A{w / 2} {e} 0 0 1 {x + w} {y + e} L{x + w} {y + h - e} '
             f'A{w / 2} {e} 0 0 1 {x} {y + h - e} Z" fill="#fff" stroke="#333" stroke-width="1.5"/>')
        s += f'<path d="M{x} {y + e} A{w / 2} {e} 0 0 0 {x + w} {y + e}" fill="none" stroke="#333" stroke-width="1.5"/>'
        s += (''.join(f'<text x="{cx + w / 2 + 8}" y="{cy - 4 + 15 * i}" font-family="{FONT}" font-size="12" fill="#222">{escape(t)}</text>' for i, t in enumerate(label.split(chr(10)))) if right
              else self._text(cx, cy + h / 2 + 16, label, size=12, valign='top'))
        self.front.append(s)
        self.el[key] = ('box', cx, cy, w / 2, h / 2)

    def note(self, x, y, w, text, attach=None, color='#555'):
        n = text.count('\n') + 1
        h = 16 * n + 12
        s = f'<path d="M{x + 12} {y} L{x} {y} L{x} {y + h} L{x + 12} {y + h}" fill="none" stroke="{color}" stroke-width="1.5"/>'
        for i, line in enumerate(text.split('\n')):
            s += f'<text x="{x + 8}" y="{y + 20 + 16 * i}" font-family="{FONT}" font-size="12" fill="{color}" font-style="italic">{escape(line)}</text>'
        if attach:
            _, ecx, ecy, _, ery = self.el[attach]
            # линия выходит из угла скобки, чтобы не перечеркивать текст сноски
            sy = y + h if ecy - ery > y + h else y if ecy + ery < y else y + h / 2
            sx = x + w if sy == y + h / 2 and ecx > x + w else x
            ax, ay = self.port(attach, attach_side(self.el[attach], sx, sy))
            s += f'<line x1="{sx}" y1="{sy}" x2="{ax}" y2="{ay}" stroke="{color}" stroke-width="1" stroke-dasharray="3 3"/>'
        self.back.append(s)

    # ---------- связи ----------
    def port(self, key, side):
        _, cx, cy, rx, ry = self.el[key]
        return {'l': (cx - rx, cy), 'r': (cx + rx, cy), 't': (cx, cy - ry), 'b': (cx, cy + ry)}[side]

    def flow(self, a, sa, b, sb, via=(), label=None, label_at=None, kind='seq'):
        pts = [self.port(a, sa), *via, self.port(b, sb)]
        if not via:
            (x1, y1), (x2, y2) = pts
            if x1 != x2 and y1 != y2:
                if sa in 'lr':
                    mx = (x1 + x2) / 2
                    pts = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)] if sb in 'lr' else [(x1, y1), (x2, y1), (x2, y2)]
                else:
                    pts = [(x1, y1), (x1, y2), (x2, y2)] if sb in 'lr' else [(x1, y1), (x1, (y1 + y2) / 2), (x2, (y1 + y2) / 2), (x2, y2)]
        d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
        if kind == 'seq':
            s = f'<path d="{d}" fill="none" stroke="#333" stroke-width="1.5" marker-end="url(#arr)"/>'
        else:
            s = f'<path d="{d}" fill="none" stroke="#555" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#open)"/>'
        if label:
            lx, ly = label_at or (pts[0][0] + 10, pts[0][1] - 8)
            s += f'<text x="{lx}" y="{ly}" font-family="{FONT}" font-size="12" fill="#333">{escape(label)}</text>'
        self.back.append(s)

    # ---------- текст ----------
    def _text(self, cx, cy, text, size=13, valign='middle'):
        lines = text.split('\n')
        lh = size + 3
        y0 = cy - lh * (len(lines) - 1) / 2 + size * 0.35 if valign == 'middle' else cy
        return ''.join(
            f'<text x="{cx}" y="{y0 + i * lh}" text-anchor="middle" font-family="{FONT}" font-size="{size}" fill="#222">{escape(t)}</text>'
            for i, t in enumerate(lines))

    def _vtext(self, x, y, text, bold=False):
        w = 'bold' if bold else 'normal'
        return (f'<text x="{x}" y="{y}" transform="rotate(-90 {x} {y})" text-anchor="middle" dominant-baseline="middle" '
                f'font-family="{FONT}" font-size="14" font-weight="{w}" fill="#222">{escape(text)}</text>')

    def legend(self, x, y, items):
        s = ''
        for i, (style, text) in enumerate(items):
            fill, stroke, dash = STYLES[style]
            yy = y + i * 26
            s += f'<rect x="{x}" y="{yy}" width="34" height="18" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-dasharray="{dash}"/>'
            s += f'<text x="{x + 44}" y="{yy + 14}" font-family="{FONT}" font-size="13" fill="#222">{escape(text)}</text>'
        self.front.append(s)

    def svg(self):
        defs = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
                '<path d="M0 0 L10 5 L0 10 z" fill="#333"/></marker>'
                '<marker id="open" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
                '<path d="M0 0 L10 5 L0 10" fill="none" stroke="#555"/></marker></defs>')
        title = f'<text x="20" y="30" font-family="{FONT}" font-size="18" font-weight="bold" fill="#222">{escape(self.title)}</text>'
        body = ''.join(self.back) + ''.join(self.front)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="#fff"/>{defs}{title}{body}</svg>')

    def save(self, name):
        svg_path = os.path.join(OUT, 'src', name + '.svg')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(self.svg())
        html = os.path.join(OUT, 'src', '_render.html')
        with open(html, 'w', encoding='utf-8') as f:
            f.write(f'<html><body style="margin:0">{self.svg()}</body></html>')
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2',
                        f'--window-size={self.w},{self.h}', f'--screenshot={os.path.join(OUT, name + ".png")}', 'file://' + html],
                       check=True, capture_output=True)
        os.remove(html)


def attach_side(el, x, y):
    _, cx, cy, rx, ry = el
    if abs(y - cy) > ry:
        return 't' if y < cy else 'b'
    return 'l' if x < cx else 'r'




# ================= AS-IS =================
d = Diagram(1960, 860, 'AS-IS: типовой процесс ревью MR с LLM-ботом без проверки замечаний (BPMN)')
X0, Y0 = 20, 50
d.pool(X0, Y0, 1910, 'Ревью MR в команде', [('Автор MR', 250), ('LLM-бот ревью', 210), ('Ревьюер', 270)])
A, B, R = Y0 + 80, Y0 + 250 + 85, Y0 + 460 + 90
d.start('s', 130, A, 'Изменения\nготовы')
d.task('a1', 260, A, 'Открыть MR')
d.task('b1', 420, B, 'Получить\nдифф MR')
d.task('b2', 610, B, 'Сгенерировать\nзамечания LLM')
d.task('b3', 800, B, 'Опубликовать\nвсе замечания в MR', 'bad')
d.task('a2', 960, A, 'Разобрать каждое\nзамечание бота', 'bad', multi=True)
d.gateway('g1', 1120, A, 'Какие\nзамечания?', kind='o')
d.task('a3', 1290, A, 'Исправить код')
d.task('a4', 1290, A + 110, 'Оспорить ложные\nзамечания в тредах', 'bad')
d.task('r1', 1290, R, 'Рассудить споры\nпо замечаниям', 'bad')
d.gateway('gm', 1450, R, None, kind='o')
d.task('r2', 1600, R, 'Проверить MR\nпо соглашениям\nвручную', 'bad')
d.gateway('g2', 1760, R, 'Есть\nнарушения?', dx=-62)
d.task('r3', 1760, R + 120, 'Одобрить MR')
d.end('e', 1880, R + 120, 'MR влит')

d.flow('s', 'r', 'a1', 'l')
d.flow('a1', 'r', 'b1', 't', via=[(420, A)])
d.flow('b1', 'r', 'b2', 'l')
d.flow('b2', 'r', 'b3', 'l')
d.flow('b3', 'r', 'a2', 'b', via=[(960, B)])
d.flow('a2', 'r', 'g1', 'l')
d.flow('g1', 'r', 'a3', 'l', label='верные', label_at=(1152, A - 8))
d.flow('g1', 'b', 'a4', 'l', via=[(1120, A + 110)], label='ложные', label_at=(1128, A + 50))
d.flow('a4', 'b', 'r1', 't')
d.flow('a3', 'r', 'gm', 't', via=[(1450, A)])
d.flow('r1', 'r', 'gm', 'l')
d.flow('gm', 'r', 'r2', 'l')
d.flow('r2', 'r', 'g2', 'l')
d.flow('g2', 't', 'a3', 't', via=[(1760, Y0 + 20), (1290, Y0 + 20)], label='да', label_at=(1768, R - 50))
d.flow('g2', 'b', 'r3', 't', label='нет', label_at=(1768, R + 48))
d.flow('r3', 'r', 'e', 'l')
d.note(560, B + 50, 170, 'ложные замечания\nпубликуются наравне\nс верными', attach='b3')
d.note(1470, Y0 + 150, 200, 'время автора и ревьюера\nуходит на спор', attach='a4')
d.note(1420, R + 80, 190, 'правила сверяются\nпо памяти ревьюера', attach='r2')
d.legend(40, Y0 + 750, [('bad', 'шаги, которые порождают ложные замечания или тратят на них время людей; в TO-BE они убраны или заменены')])
d.save('bpmn-as-is')

# ================= TO-BE =================
d = Diagram(2290, 960, 'TO-BE: ревью MR с мультиагентной системой и проверкой каждого замечания (BPMN)')
d.pool(X0, Y0, 2250, 'Ревью MR в команде', [('Автор MR', 180), ('Система ревью (контур компании)', 470), ('Ревьюер', 200)])
ST = Y0 + 180
A, B1, R = Y0 + 90, ST + 130, Y0 + 650 + 100
d.start('s', 110, A, 'Изменения\nготовы')
d.task('a1', 230, A, 'Открыть MR')
d.gateway('gx', 400, A, None)
d.store('conv', 400, ST + 290, 'Соглашения\nкоманды')
d.task('m1', 400, B1, 'Получить дифф\nи применимые правила')
d.task('m2', 590, B1, 'Найти нарушения\nагентами по темам', 'new')
d.subprocess('sp', 700, ST + 40, 570, 310, 'Проверить каждое замечание', 'new')
d.start('i0', 740, B1, '')
d.task('i1', 870, B1, 'Проверить замечание\nпо коду и правилу', 'new')
d.gateway('i2', 1020, B1, 'Подтверждено?')
d.task('i3', 1170, B1, 'Пометить\nподтвержденным')
d.end('i4', 1170, B1 + 85, '')
d.task('i5', 1020, B1 + 150, 'Записать отклонение\nс причиной', 'new')
d.end('i6', 1180, B1 + 150, '')
d.error_boundary('ie', 830, B1 + 33, '')
d.error_end('ie2', 830, B1 + 150, 'ошибка\nмодели')
d.error_boundary('err', 760, ST + 350, 'ошибка модели')
d.task('m6', 900, ST + 415, 'Отметить прогон\nошибкой', 'new')
d.gateway('gp', 1340, B1, 'Есть\nподтвержденные?')
d.task('m5', 1500, B1, 'Опубликовать треды\nс номером правила', 'new')
d.store('log', 1500, ST + 290, 'Журнал\nпрогонов', right=True)
d.task('a2', 1500, A, 'Исправить код\nили оспорить замечание')
d.gateway('ga', 1680, A, 'Код\nизменен?', dx=50)
d.gateway('gm', 1640, R, None)
d.task('r1', 1800, R, 'Проверить требования,\nспорные замечания,\nсоглашения выборочно', 'new')
d.gateway('g2', 1960, R, 'Есть\nзамечания?', label_pos='bottom')
d.task('r2', 2100, R, 'Одобрить MR')
d.end('e', 2215, R, 'MR влит')

d.flow('s', 'r', 'a1', 'l')
d.flow('a1', 'r', 'gx', 'l')
d.flow('gx', 'b', 'm1', 't')
d.flow('conv', 't', 'm1', 'b', kind='assoc')
d.flow('m1', 'r', 'm2', 'l')
d.flow('m2', 'r', 'sp', 'l')
d.flow('i0', 'r', 'i1', 'l')
d.flow('i1', 'r', 'i2', 'l')
d.flow('i2', 'r', 'i3', 'l', label='да')
d.flow('i3', 'b', 'i4', 't')
d.flow('i2', 'b', 'i5', 't', label='нет', label_at=(1028, B1 + 48))
d.flow('i5', 'r', 'i6', 'l')
d.flow('err', 'b', 'm6', 'l', via=[(760, ST + 415)])
d.flow('sp', 'r', 'gp', 'l')
d.flow('gp', 'r', 'm5', 'l', label='да')
d.flow('m5', 'b', 'log', 't', kind='assoc')
d.flow('m5', 't', 'a2', 'b')
d.flow('a2', 'r', 'ga', 'l')
d.flow('ga', 't', 'gx', 't', via=[(1680, Y0 + 40), (400, Y0 + 40)], label='да: новый коммит, повторный прогон', label_at=(900, Y0 + 34))
d.flow('ga', 'b', 'gm', 'b', via=[(1680, R + 60), (1640, R + 60)], label='нет, оспорено', label_at=(1688, A + 50))
d.flow('ie', 'b', 'ie2', 't')
d.flow('i5', 'b', 'log', 'b', via=[(1020, ST + 372), (1500, ST + 372)], kind='assoc')
d.flow('gp', 'b', 'gm', 'l', via=[(1340, R)], label='нет', label_at=(1348, B1 + 48))
d.flow('m6', 'r', 'gm', 't', via=[(1640, ST + 415)])
d.flow('gm', 'r', 'r1', 'l')
d.flow('r1', 'r', 'g2', 'l')
d.flow('g2', 't', 'a2', 't', via=[(1960, Y0 + 20), (1500, Y0 + 20)], label='да', label_at=(1968, R - 40))
d.flow('g2', 'r', 'r2', 'l', label='нет')
d.flow('r2', 'r', 'e', 'l')
d.note(470, ST + 12, 220, 'агенты по темам: архитектура,\nкод и именование, тесты,\nкомментарии', attach='m2')
d.note(430, ST + 380, 240, 'ошибка модели, лимит времени или\nневалидный ответ: замечания\nне публикуются, MR не блокируется', attach='m6')
d.note(1730, Y0 + 660, 190, 'полнота системы ниже 100 %,\nпоэтому выборочно', attach='r1')
d.legend(40, Y0 + 870, [('new', 'новые или измененные шаги: проверка каждого замечания отдельно, журнал, обработка сбоя, ревьюер смотрит требования задачи')])
d.save('bpmn-to-be')
