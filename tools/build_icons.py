"""Irminsul: builds the file icon theme from the drawings in docs/icons.html (approved 15 Oct 2026).

The <defs> block in docs/icons.html is the single source of the drawings. Change a symbol there, then run
    python tools/build_icons.py
It writes icons/*.svg (one per icon, folders with their emblem baked in) and two icon themes:
themes/irminsul-icon-theme.json (Night folders) and themes/irminsul-icon-theme-parchment.json (Parchment folders).
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SHEET = HERE / 'docs' / 'icons.html'
OUT = HERE / 'icons'

# icon name -> symbol in the sheet
FILES = {
    'python': 's-drop', 'javascript': 's-gem', 'typescript': 's-gemblue', 'html': 's-flame', 'css': 's-swirl', 'json': 's-bolt',
    'settings': 's-gear', 'skript': 's-block', 'markdown': 's-md', 'readme': 's-book', 'claude': 's-star', 'text': 's-txt',
    'image': 's-image', 'script': 's-term', 'git': 's-branch', 'package': 's-parcel', 'archive': 's-chest', 'pdf': 's-pdf',
    'audio': 's-note', 'video': 's-film', 'file': 's-default',
}
EXTENSIONS = {
    'python': 'py pyw pyi', 'javascript': 'js mjs cjs jsx', 'typescript': 'ts tsx mts cts', 'html': 'html htm', 'css': 'css scss sass less',
    'json': 'json jsonc json5', 'settings': 'ini cfg conf toml yml yaml env properties', 'skript': 'sk', 'markdown': 'md markdown',
    'text': 'txt log', 'image': 'png jpg jpeg gif webp svg ico bmp', 'script': 'ps1 psm1 psd1 bat cmd sh', 'archive': 'zip 7z rar tar gz',
    'pdf': 'pdf', 'audio': 'mp3 wav ogg flac m4a', 'video': 'mp4 webm mov mkv avi',
}
FILE_NAMES = {'claude.md': 'claude', 'readme.md': 'readme', 'package.json': 'package', 'package-lock.json': 'package',
              '.gitignore': 'git', '.gitattributes': 'git', '.gitmodules': 'git'}
LANGUAGES = {'python': 'python', 'javascript': 'javascript', 'typescript': 'typescript', 'html': 'html', 'css': 'css', 'json': 'json',
             'jsonc': 'json', 'markdown': 'markdown', 'skript': 'skript', 'powershell': 'script', 'bat': 'script', 'shellscript': 'script',
             'yaml': 'settings', 'ini': 'settings', 'plaintext': 'text'}
# folder name -> emblem symbol
EMBLEMS = {'docs': 's-book', 'doc': 's-book', 'tests': 's-flask', 'test': 's-flask', '__tests__': 's-flask', 'tools': 's-hammer',
           'themes': 's-palette', '.claude': 's-star', 'art': 's-image', 'images': 's-image', 'assets': 's-image', 'scripts': 's-block',
           '.git': 's-branch'}
EMBLEM_NAME = {'s-book': 'docs', 's-flask': 'tests', 's-hammer': 'tools', 's-palette': 'themes', 's-star': 'claude',
               's-image': 'art', 's-block': 'scripts', 's-branch': 'git'}


def read_sheet():
    defs = re.search(r'<defs>(.*?)</defs>', SHEET.read_text(encoding='utf-8'), re.S).group(1)
    grads = {m.group(1): m.group(0) for m in re.finditer(r'<linearGradient id="([^"]+)".*?</linearGradient>', defs, re.S)}
    syms = {m.group(1): m.group(0) for m in re.finditer(r'<symbol id="([^"]+)".*?</symbol>', defs, re.S)}
    return grads, syms


def svg(uses, grads, syms):
    """One standalone 16x16 SVG: the symbols it uses (and theirs, recursively) plus the gradients they need."""
    need, todo = [], [u[0] for u in uses]
    while todo:
        sid = todo.pop()
        if sid in need:
            continue
        need.append(sid)
        todo += re.findall(r'href="#([^"]+)"', syms[sid])
    body = ''.join(syms[s] for s in need)
    g = sorted(set(re.findall(r'url\(#([^)]+)\)', body)))
    use = ''.join('<use href="#%s"%s/>' % (sid, extra) for sid, extra in uses)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><defs>' +
            ''.join(grads[x] for x in g) + body + '</defs>' + use + '</svg>\n')


def build():
    grads, syms = read_sheet()
    OUT.mkdir(exist_ok=True)
    written = {}

    def write(name, uses):
        (OUT / (name + '.svg')).write_text(svg(uses, grads, syms), encoding='utf-8')
        written[name] = True

    for name, sid in FILES.items():
        write(name, [(sid, '')])
    for style in ('night', 'cream'):
        for open_ in (False, True):
            base = 'f-%s%s' % (style, '-open' if open_ else '')
            write('folder-%s%s' % (style, '-open' if open_ else ''), [(base, '')])
            for em, label in EMBLEM_NAME.items():
                y = 6.6 if open_ else 5.9
                write('folder-%s-%s%s' % (style, label, '-open' if open_ else ''),
                      [(base, ''), (em, ' x="6.6" y="%s" width="9.4" height="9.4"' % y)])

    out = []
    for style, fname, label in (('night', 'irminsul-icon-theme.json', 'Night folders'),
                                ('cream', 'irminsul-icon-theme-parchment.json', 'Parchment folders')):
        defs = {'_' + n: {'iconPath': '../icons/%s.svg' % n} for n in FILES}
        for n in ('folder-%s' % style, 'folder-%s-open' % style):
            defs['_' + n] = {'iconPath': '../icons/%s.svg' % n}
        folder_names, folder_open = {}, {}
        for folder, em in EMBLEMS.items():
            n = 'folder-%s-%s' % (style, EMBLEM_NAME[em])
            defs['_' + n] = {'iconPath': '../icons/%s.svg' % n}
            defs['_' + n + '-open'] = {'iconPath': '../icons/%s-open.svg' % n}
            folder_names[folder] = '_' + n
            folder_open[folder] = '_' + n + '-open'
        theme = {
            'iconDefinitions': defs,
            'file': '_file', 'folder': '_folder-%s' % style, 'folderExpanded': '_folder-%s-open' % style,
            'rootFolder': '_folder-%s' % style, 'rootFolderExpanded': '_folder-%s-open' % style,
            'fileExtensions': {ext: '_' + n for n, exts in EXTENSIONS.items() for ext in exts.split()},
            'fileNames': {k: '_' + v for k, v in FILE_NAMES.items()},
            'languageIds': {k: '_' + v for k, v in LANGUAGES.items()},
            'folderNames': folder_names, 'folderNamesExpanded': folder_open,
        }
        (HERE / 'themes' / fname).write_text(json.dumps(theme, indent=2) + '\n', encoding='utf-8')
        out.append('%s (%s): %d icons, %d extensions, %d special folders' % (fname, label, len(defs), len(theme['fileExtensions']), len(folder_names)))
    out.append('icons/: %d SVG files' % len(written))
    return out


if __name__ == '__main__':
    print('\n'.join(build()))
