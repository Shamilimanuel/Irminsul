"""Irminsul: measures how readable every text colour is against the background it sits on.

    python tools/check_contrast.py

Contrast ratio is the WCAG measure: 1:1 is invisible, 21:1 is black on white. 4.5:1 is the bar for normal text,
3:1 for large or less important text (line numbers, comments, faint labels). Reads the palettes from build_themes.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_themes import VARIANTS, MC, all_themes  # noqa: E402


def luminance(hex6):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def blend(fg, bg):
    """A #RRGGBBAA colour laid over a solid background, as the screen shows it."""
    if len(fg) == 7:
        return fg
    al = int(fg[7:9], 16) / 255
    return '#' + ''.join('%02X' % round(int(fg[i:i + 2], 16) * al + int(bg[i:i + 2], 16) * (1 - al)) for i in (1, 3, 5))


def ratio(fg, bg):
    l1, l2 = sorted((luminance(blend(fg, bg)), luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# (what it is, text key, background key, minimum). 3.0 = quiet/large text, 4.5 = normal text.
PAIRS = [
    ('Code text on editor', 'fg', 'ed', 4.5), ('Code text on current line', 'fg', 'hl', 4.5),
    ('Electro keywords', 'k', 'ed', 4.5), ('Electro, deeper (def, class)', 'kd', 'ed', 4.5), ('Geo functions', 'f', 'ed', 4.5), ('Dendro strings', 's', 'ed', 4.5),
    ('Pyro numbers', 'n', 'ed', 4.5), ('Hydro types', 't', 'ed', 4.5), ('Cryo properties', 'p', 'ed', 4.5),
    ('Anemo decorators', 'd', 'ed', 4.5), ('Operators', 'o', 'ed', 4.5), ('Comments', 'c', 'ed', 3.0),
    ('Comments on current line', 'c', 'hl', 3.0), ('Line numbers', 'fg3', 'ed', 3.0), ('Active line number', 'acc', 'ed', 4.5),
    ('Side bar text', 'fg', 'side', 4.5), ('Side bar dim text', 'fg2', 'side', 4.5), ('Inactive tab', 'fg2', 'tab', 4.5),
    ('Activity bar inactive icon', 'fg3', 'act', 3.0), ('Status bar text', 'statusFg', 'status', 4.5),
    ('Popup text', 'fg', 'widget', 4.5), ('Popup dim text', 'fg2', 'widget', 4.5), ('Input placeholder', 'fg3', 'input', 3.0),
    ('Button text on accent', 'accFg', 'acc', 4.5), ('Error text', 'err', 'ed', 4.5), ('Terminal text', 'fg', 'term', 4.5),
    ('Code text on selection', 'fg', ('sel', 'ed'), 4.5), ('Strings on selection', 's', ('sel', 'ed'), 4.5),
    ('Comments on selection', 'c', ('sel', 'ed'), 3.0),
]


# Terminal pairs (Claude Code's dark ANSI theme): (what, text, background, minimum); names are keys of P['ansi'], 'term' = background.
# A text name ending in ':dim' is drawn the way VS Code draws dim text: half strength over the background (measured on a real
# session, 15 Oct: quiet lines came out exactly halfway). VS Code's automatic contrast fix does not lift dim text.
TERM = [
    ('Terminal main text', 'brightWhite', 'term', 4.5), ('Quiet lines (dimmed)', 'white:dim', 'term', 3.5),
    ('git / test colours', 'red', 'term', 4.5), ('', 'green', 'term', 4.5), ('', 'yellow', 'term', 4.5), ('', 'blue', 'term', 4.5),
    ('', 'magenta', 'term', 4.5), ('', 'cyan', 'term', 4.5),
    ('Claude / errors', 'brightRed', 'term', 4.5), ('Success dots', 'brightGreen', 'term', 4.5), ('Warnings', 'brightYellow', 'term', 4.5),
    ('Links / permission', 'brightBlue', 'term', 4.5), ('Auto mode / skills', 'brightMagenta', 'term', 4.5), ('Code in replies', 'brightCyan', 'term', 4.5),
    ('Your message bar', 'brightWhite', 'brightBlack', 4.5),
    ('Added word', 'black', 'brightGreen', 4.5), ('Removed word', 'black', 'brightRed', 4.5),
]


def check():
    bad = 0
    for key, P in VARIANTS.items():
        print('\n%s' % P['label'])
        for name, fgk, bgk, need in PAIRS:
            bg = blend(P[bgk[0]], P[bgk[1]]) if isinstance(bgk, tuple) else P[bgk]
            r = ratio(P[fgk], bg)
            ok = r >= need
            bad += not ok
            print('  %-4s %-30s %5.2f:1  (needs %.1f)' % ('ok' if ok else 'LOW', name, r, need))
        A = dict(P['ansi'], term=P['term'])
        for name, fgk, bgk, need in TERM:
            fg = A[fgk.split(':')[0]]
            if fgk.endswith(':dim'):
                fg = blend(fg + '80', A[bgk])
            name = name or '  ' + fgk
            r = ratio(fg, A[bgk])
            ok = r >= need
            bad += not ok
            print('  %-4s %-30s %5.2f:1  (needs %.1f)' % ('ok' if ok else 'LOW', name, r, need))
        low = [(code, ratio(col, P['ed'])) for code, col in MC.items() if ratio(col, P['ed']) < 3.0]
        bad += len(low)
        for code, r in low:
            print('  LOW  Minecraft &%s                    %5.2f:1  (needs 3.0)' % (code, r))
        print('  %-4s Minecraft colour codes &0-&f   lowest %.2f:1  (needs 3.0)' % ('ok' if not low else 'LOW', min(ratio(v, P['ed']) for v in MC.values())))
    print('\nElement accent versions (button text on the accent, active line number on the editor)')
    for fname, P in all_themes():
        if P['label'] in (VARIANTS['night']['label'], VARIANTS['abyss']['label']):
            continue  # the two base variants are checked above
        r1, r2 = ratio(P['accFg'], P['acc']), ratio(P['acc'], P['ed'])
        ok = r1 >= 4.5 and r2 >= 4.5
        bad += not ok
        print('  %-4s %-30s %5.2f:1 / %5.2f:1  (needs 4.5)' % ('ok' if ok else 'LOW', P['label'], r1, r2))
    print('\n%s' % ('All readable.' if not bad else '%d pair(s) below the bar.' % bad))
    return bad


if __name__ == '__main__':
    sys.exit(1 if check() else 0)
