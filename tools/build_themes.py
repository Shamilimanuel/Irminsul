"""Irminsul: builds the VS Code theme files from one palette per variant.

The palettes below are the single source of truth. Change a colour here, run this script, reload VS Code.
    python tools/build_themes.py
It writes themes/irminsul-night-color-theme.json and themes/irminsul-abyss-color-theme.json.

Code colours follow the seven elements (approved preview, docs/preview.html, 15 Oct 2026):
  Electro = keywords, Geo = functions, Dendro = strings, Pyro = numbers & constants,
  Hydro = types & classes, Cryo = properties, Anemo = decorators & special. Comments: quiet and italic.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

VARIANTS = {
    'night': {
        'label': 'Irminsul Night',
        # surfaces, back to front
        'ed': '#161B27', 'side': '#11151F', 'act': '#0D1018', 'bar': '#0D1018', 'tab': '#11151F', 'tabOn': '#161B27',
        'term': '#11151F', 'widget': '#1A2030', 'input': '#0F131C', 'status': '#1A2031',
        # text
        'fg': '#E4DDCD', 'fg2': '#9DA1B0', 'fg3': '#676E86', 'statusFg': '#E4DDCD',
        # lines, highlight, accent
        'hl': '#1D2332', 'sel': '#D3BC8E2E', 'selHi': '#D3BC8E1F', 'bd': '#232A3B', 'acc': '#D3BC8E', 'acc2': '#F3D79C', 'accFg': '#1A1F2C',
        # the seven elements, plus comments and operators
        'k': '#B18BEC', 'kd': '#9479D9', 'f': '#F2C463', 's': '#A8D04A', 'n': '#FF8A5C', 't': '#5CC4F5', 'p': '#9FE0F0', 'd': '#5FD3AE', 'c': '#7B83A1', 'o': '#C9BFA9',
        # git / problems (kept in the element family)
        'add': '#A8D04A', 'mod': '#F2C463', 'del': '#FF8A5C', 'err': '#FF6B6B', 'warn': '#F2C463', 'info': '#5CC4F5',
        # terminal (checked against a real Claude Code session, 15 Oct): normal colours a step below the bright element colours.
        # white is what Claude Code dims for quiet lines; VS Code draws dim text at half strength, so white is kept bright.
        # bright white = main text, bright black = the bar behind your own messages in Claude Code.
        'ansi': {'black': '#0D1018', 'red': '#C16D6D', 'green': '#699139', 'yellow': '#A77F2F', 'blue': '#378BC3', 'magenta': '#9873D1',
                 'cyan': '#3791A5', 'white': '#D8DADF', 'brightBlack': '#383E52', 'brightRed': '#FF8A5C', 'brightGreen': '#A8D04A',
                 'brightYellow': '#F3D79C', 'brightBlue': '#5CC4F5', 'brightMagenta': '#B18BEC', 'brightCyan': '#5FD3AE', 'brightWhite': '#E4DDCD'},
    },
    'abyss': {
        'label': 'Irminsul Abyss',
        'ed': '#16121F', 'side': '#110E19', 'act': '#0C0A13', 'bar': '#0C0A13', 'tab': '#110E19', 'tabOn': '#16121F',
        'term': '#110E19', 'widget': '#1D1729', 'input': '#0E0B15', 'status': '#221A33',
        'fg': '#E6DEEF', 'fg2': '#A29CB3', 'fg3': '#6B6485', 'statusFg': '#E6DEEF',
        'hl': '#201A2D', 'sel': '#B18BEC33', 'selHi': '#B18BEC24', 'bd': '#261F36', 'acc': '#B18BEC', 'acc2': '#D7C2FA', 'accFg': '#160F22',
        'k': '#D7A6FF', 'kd': '#A97FE0', 'f': '#F2C463', 's': '#9ED65B', 'n': '#FF8F7A', 't': '#6FC8F7', 'p': '#A9E3F1', 'd': '#67D9B6', 'c': '#7D7499', 'o': '#C8BFD8',
        'add': '#9ED65B', 'mod': '#F2C463', 'del': '#FF8F7A', 'err': '#FF6B7A', 'warn': '#F2C463', 'info': '#6FC8F7',
        'ansi': {'black': '#0C0A13', 'red': '#C46A78', 'green': '#63913C', 'yellow': '#A77F2F', 'blue': '#348BC5', 'magenta': '#9B71D0',
                 'cyan': '#3691A5', 'white': '#DBD8E1', 'brightBlack': '#3A3450', 'brightRed': '#FF8F7A', 'brightGreen': '#9ED65B',
                 'brightYellow': '#F2C463', 'brightBlue': '#6FC8F7', 'brightMagenta': '#D7A6FF', 'brightCyan': '#67D9B6', 'brightWhite': '#E6DEEF'},
    },
}


def a(hex6, alpha):
    """#RRGGBB plus an alpha in 0..1 → #RRGGBBAA."""
    return hex6[:7] + '%02X' % round(alpha * 255)


def colors(P):
    return {
        # base
        'focusBorder': a(P['acc'], .6), 'foreground': P['fg'], 'descriptionForeground': P['fg2'], 'errorForeground': P['err'],
        'icon.foreground': P['fg2'], 'selection.background': P['sel'], 'widget.shadow': '#00000066', 'sash.hoverBorder': P['acc'],
        'textLink.foreground': P['t'], 'textLink.activeForeground': P['acc2'], 'textPreformat.foreground': P['f'], 'textBlockQuote.background': P['widget'],
        'textBlockQuote.border': P['acc'], 'textCodeBlock.background': P['input'],
        # window / title / activity
        'titleBar.activeBackground': P['bar'], 'titleBar.activeForeground': P['fg2'], 'titleBar.inactiveBackground': P['bar'], 'titleBar.inactiveForeground': P['fg3'], 'titleBar.border': P['bd'],
        'activityBar.background': P['act'], 'activityBar.foreground': P['fg'], 'activityBar.inactiveForeground': P['fg3'], 'activityBar.border': P['bd'],
        'activityBar.activeBorder': P['acc'], 'activityBarBadge.background': P['acc'], 'activityBarBadge.foreground': P['accFg'],
        # side bar
        'sideBar.background': P['side'], 'sideBar.foreground': P['fg'], 'sideBar.border': P['bd'], 'sideBarTitle.foreground': P['fg2'],
        'sideBarSectionHeader.background': P['side'], 'sideBarSectionHeader.foreground': P['fg2'], 'sideBarSectionHeader.border': P['bd'],
        'list.activeSelectionBackground': P['hl'], 'list.activeSelectionForeground': P['fg'], 'list.inactiveSelectionBackground': P['hl'],
        'list.hoverBackground': a(P['hl'], .7), 'list.focusOutline': P['acc'], 'list.highlightForeground': P['acc2'], 'list.errorForeground': P['err'],
        'list.warningForeground': P['warn'], 'tree.indentGuidesStroke': P['bd'],
        # tabs & breadcrumbs
        'editorGroupHeader.tabsBackground': P['tab'], 'editorGroupHeader.tabsBorder': P['bd'], 'editorGroup.border': P['bd'],
        'tab.activeBackground': P['tabOn'], 'tab.activeForeground': P['fg'], 'tab.activeBorderTop': P['acc'], 'tab.inactiveBackground': P['tab'],
        'tab.inactiveForeground': P['fg2'], 'tab.border': P['bd'], 'tab.hoverBackground': P['tabOn'], 'tab.unfocusedActiveBorderTop': a(P['acc'], .4),
        'tab.activeModifiedBorder': P['acc'], 'breadcrumb.foreground': P['fg2'], 'breadcrumb.focusForeground': P['fg'], 'breadcrumb.activeSelectionForeground': P['acc2'],
        'breadcrumbPicker.background': P['widget'],
        # editor
        'editor.background': P['ed'], 'editor.foreground': P['fg'], 'editorLineNumber.foreground': P['fg3'], 'editorLineNumber.activeForeground': P['acc'],
        'editorCursor.foreground': P['acc2'], 'editor.selectionBackground': P['sel'], 'editor.inactiveSelectionBackground': P['selHi'],
        'editor.selectionHighlightBackground': P['selHi'], 'editor.wordHighlightBackground': P['selHi'], 'editor.wordHighlightStrongBackground': a(P['k'], .18),
        'editor.lineHighlightBackground': P['hl'], 'editor.lineHighlightBorder': '#00000000', 'editor.findMatchBackground': a(P['f'], .35),
        'editor.findMatchHighlightBackground': a(P['f'], .16), 'editor.rangeHighlightBackground': a(P['acc'], .08), 'editor.hoverHighlightBackground': a(P['t'], .12),
        'editorBracketMatch.background': a(P['acc'], .15), 'editorBracketMatch.border': a(P['acc'], .6), **{'editorIndentGuide.background%d' % (i + 1): a(P[e], .28) for i, e in enumerate('fktdnp')},
        **{'editorIndentGuide.activeBackground%d' % (i + 1): a(P[e], .75) for i, e in enumerate('fktdnp')},
        'editorUnnecessaryCode.opacity': '#00000080',  # pick 3: unused code fades to half 'editorWhitespace.foreground': P['fg3'], 'editorRuler.foreground': P['bd'],
        'editorBracketHighlight.foreground1': P['f'], 'editorBracketHighlight.foreground2': P['k'], 'editorBracketHighlight.foreground3': P['t'],
        'editorBracketHighlight.foreground4': P['d'], 'editorBracketHighlight.foreground5': P['n'], 'editorBracketHighlight.foreground6': P['p'],
        'editorError.foreground': P['err'], 'editorWarning.foreground': P['warn'], 'editorInfo.foreground': P['info'], 'editorHint.foreground': P['d'],
        'editorGutter.addedBackground': P['add'], 'editorGutter.modifiedBackground': P['mod'], 'editorGutter.deletedBackground': P['del'],
        'editorOverviewRuler.border': '#00000000', 'editorOverviewRuler.addedForeground': a(P['add'], .6), 'editorOverviewRuler.modifiedForeground': a(P['mod'], .6),
        'editorOverviewRuler.deletedForeground': a(P['del'], .6), 'editorOverviewRuler.errorForeground': P['err'], 'editorOverviewRuler.warningForeground': P['warn'],
        'editorCodeLens.foreground': P['fg3'], 'editorInlayHint.background': a(P['widget'], .8), 'editorInlayHint.foreground': P['fg2'],
        'editorWidget.background': P['widget'], 'editorWidget.border': P['bd'], 'editorHoverWidget.background': P['widget'], 'editorHoverWidget.border': P['bd'],
        'editorSuggestWidget.background': P['widget'], 'editorSuggestWidget.border': P['bd'], 'editorSuggestWidget.selectedBackground': P['hl'],
        'editorSuggestWidget.highlightForeground': P['acc2'], 'editorSuggestWidget.foreground': P['fg'],
        'minimap.selectionHighlight': a(P['acc'], .5), 'minimapSlider.background': a(P['fg3'], .25), 'minimapSlider.hoverBackground': a(P['fg3'], .35),
        'scrollbarSlider.background': a(P['fg3'], .3), 'scrollbarSlider.hoverBackground': a(P['fg3'], .45), 'scrollbarSlider.activeBackground': a(P['acc'], .45),
        'peekView.border': P['acc'], 'peekViewEditor.background': P['side'], 'peekViewResult.background': P['side'], 'peekViewTitle.background': P['widget'],
        'peekViewEditor.matchHighlightBackground': a(P['f'], .25), 'peekViewResult.matchHighlightBackground': a(P['f'], .25),
        'diffEditor.insertedTextBackground': a(P['add'], .14), 'diffEditor.removedTextBackground': a(P['del'], .14),
        # inputs, buttons, dropdowns, badges
        'input.background': P['input'], 'input.foreground': P['fg'], 'input.border': P['bd'], 'input.placeholderForeground': P['fg3'],
        'inputOption.activeBorder': P['acc'], 'inputOption.activeBackground': a(P['acc'], .2), 'inputValidation.errorBorder': P['err'],
        'button.background': P['acc'], 'button.foreground': P['accFg'], 'button.hoverBackground': P['acc2'], 'button.secondaryBackground': P['widget'],
        'button.secondaryForeground': P['fg'], 'button.secondaryHoverBackground': P['hl'], 'dropdown.background': P['widget'], 'dropdown.border': P['bd'],
        'dropdown.foreground': P['fg'], 'checkbox.background': P['input'], 'checkbox.border': P['bd'], 'badge.background': P['acc'], 'badge.foreground': P['accFg'],
        'progressBar.background': P['acc'], 'quickInput.background': P['widget'], 'quickInputList.focusBackground': P['hl'], 'pickerGroup.foreground': P['acc'],
        'pickerGroup.border': P['bd'], 'keybindingLabel.background': P['input'], 'keybindingLabel.border': P['bd'], 'keybindingLabel.foreground': P['fg'],
        'menu.background': P['widget'], 'menu.foreground': P['fg'], 'menu.selectionBackground': P['hl'], 'menu.selectionForeground': P['acc2'], 'menu.separatorBackground': P['bd'],
        'notifications.background': P['widget'], 'notifications.border': P['bd'], 'notificationCenterHeader.background': P['side'], 'notificationLink.foreground': P['t'],
        # panel & terminal
        'panel.background': P['term'], 'panel.border': P['bd'], 'panelTitle.activeForeground': P['fg'], 'panelTitle.activeBorder': P['acc'],
        'panelTitle.inactiveForeground': P['fg2'], 'terminal.background': P['term'], 'terminal.foreground': P['fg'], 'terminalCursor.foreground': P['acc2'],
        'terminal.selectionBackground': P['sel'],
        **{'terminal.ansi' + k[0].upper() + k[1:]: v for k, v in P['ansi'].items()},
        # status bar
        'statusBar.background': P['status'], 'statusBar.foreground': P['statusFg'], 'statusBar.border': P['bd'], 'statusBar.noFolderBackground': P['status'],
        'statusBar.debuggingBackground': P['n'], 'statusBar.debuggingForeground': P['accFg'], 'statusBarItem.remoteBackground': P['acc'],
        'statusBarItem.remoteForeground': P['accFg'], 'statusBarItem.hoverBackground': a(P['fg'], .1), 'statusBarItem.errorBackground': P['err'],
        # small gaps found by comparing with Claude Dark (15 Oct)
        'editor.snippetTabstopHighlightBackground': a(P['acc'], .15), 'editor.snippetTabstopHighlightBorder': a(P['acc'], .5),
        'editor.snippetFinalTabstopHighlightBackground': a(P['d'], .12), 'editor.snippetFinalTabstopHighlightBorder': a(P['d'], .5),
        'extensionButton.prominentBackground': P['acc'], 'extensionButton.prominentForeground': P['accFg'], 'extensionButton.prominentHoverBackground': P['acc2'],
        'extensionButton.background': P['acc'], 'extensionButton.foreground': P['accFg'], 'extensionButton.hoverBackground': P['acc2'],
        'list.focusBackground': P['hl'], 'list.hoverForeground': P['fg'], 'list.inactiveSelectionForeground': P['fg'],
        'editorHoverWidget.foreground': P['fg'], 'editorHoverWidget.highlightForeground': P['acc2'],
        'editorIndentGuide.background': a(P['f'], .28), 'editorIndentGuide.activeBackground': a(P['f'], .75),
        'editorSuggestWidget.focusHighlightForeground': P['acc2'], 'editorSuggestWidget.selectedForeground': P['fg'],
        'editorGutter.background': P['ed'], 'menubar.selectionBackground': P['hl'], 'notifications.foreground': P['fg'],
        'scrollbar.shadow': '#00000066', 'statusBarItem.activeBackground': a(P['fg'], .18),
        # git decorations
        'gitDecoration.addedResourceForeground': P['add'], 'gitDecoration.modifiedResourceForeground': P['mod'], 'gitDecoration.deletedResourceForeground': P['del'],
        'gitDecoration.untrackedResourceForeground': P['d'], 'gitDecoration.ignoredResourceForeground': P['fg3'], 'gitDecoration.conflictingResourceForeground': P['k'],
    }


def token_colors(P):
    def rule(name, scope, fg, style=None):
        r = {'name': name, 'scope': scope, 'settings': {'foreground': fg}}
        if style:
            r['settings']['fontStyle'] = style
        return r
    return [
        rule('Comments (a whisper in the margin)', ['comment', 'punctuation.definition.comment', 'string.quoted.docstring'], P['c'], 'italic'),
        rule('Electro: keywords that steer (if, for, return, import)', ['keyword', 'keyword.control', 'keyword.operator.new', 'keyword.operator.expression',
                                    'keyword.operator.logical.python', 'keyword.other.special-method', 'variable.language.this'], P['k']),
        rule('Electro, deeper: keywords that create (def, class, const, let)', ['storage.type', 'storage.modifier', 'keyword.declaration',
                                    'storage.type.function', 'storage.type.class'], P['kd']),
        rule('Async and await go italic', ['storage.modifier.async', 'storage.type.function.async', 'keyword.control.flow.await',
                                           'keyword.control.await', 'keyword.operator.await'], P['kd'], 'italic'),
        rule('Geo: functions', ['entity.name.function', 'support.function', 'meta.function-call entity.name.function', 'entity.name.method',
                                'support.function.builtin', 'entity.other.attribute-name.class.css'], P['f']),
        rule('Dendro: strings', ['string', 'string.quoted', 'string.template', 'punctuation.definition.string', 'markup.inline.raw'], P['s']),
        rule('Pyro: numbers & constants', ['constant.numeric', 'constant.language', 'constant.character', 'constant.other', 'support.constant',
                                           'variable.other.constant', 'keyword.other.unit', 'constant.other.color'], P['n']),
        rule('Hydro: types & classes', ['entity.name.type', 'entity.name.class', 'support.type', 'support.class', 'entity.other.inherited-class',
                                        'storage.type.primitive', 'entity.name.tag', 'support.type.property-name.json'], P['t']),
        rule('Cryo: properties', ['variable.other.property', 'variable.other.object.property', 'support.variable.property', 'meta.property-name',
                                  'support.type.property-name', 'entity.other.attribute-name', 'variable.parameter', 'variable.language.self'], P['p']),
        rule('Anemo: decorators & special', ['entity.name.function.decorator', 'meta.decorator', 'punctuation.decorator', 'punctuation.definition.template-expression',
                                             'variable.other.constant.property', 'variable.css', 'variable.scss', 'entity.other.attribute-name.pseudo-class',
                                             'constant.character.escape', 'string.regexp'], P['d']),
        rule('Operators & punctuation', ['keyword.operator', 'punctuation', 'meta.brace', 'punctuation.separator', 'punctuation.terminator'], P['o']),
        rule('Variables', ['variable', 'variable.other.readwrite', 'meta.definition.variable'], P['fg']),
        rule('Object keys ({ name: 1 })', ['meta.object-literal.key'], P['p']),
        rule('Fenced code: the language name and the backticks', ['fenced_code.block.language', 'punctuation.definition.markdown'], P['d']),
        rule('Markdown headings', ['markup.heading', 'entity.name.section'], P['acc2'], 'bold'),
        rule('Markdown ## in Hydro', ['heading.2.markdown', 'heading.2.markdown entity.name.section', 'heading.2.markdown punctuation.definition.heading',
                                      'markup.heading.2'], P['t'], 'bold'),
        rule('Markdown ### in Anemo', ['heading.3.markdown', 'heading.3.markdown entity.name.section', 'heading.3.markdown punctuation.definition.heading',
                                       'markup.heading.3'], P['d'], 'bold'),
        rule('Markdown #### and deeper in Cryo', ['heading.4.markdown', 'heading.5.markdown', 'heading.6.markdown', 'heading.4.markdown entity.name.section',
                                                  'heading.5.markdown entity.name.section', 'heading.6.markdown entity.name.section'], P['p'], 'bold'),
        rule('Markdown bold / italic', ['markup.bold'], P['f'], 'bold'),
        rule('Markdown italic', ['markup.italic'], P['k'], 'italic'),
        rule('Markdown links', ['markup.underline.link', 'string.other.link'], P['t']),
        rule('Markdown quotes & lists', ['markup.quote', 'punctuation.definition.list'], P['d']),
        rule('Diff added', ['markup.inserted'], P['add']), rule('Diff removed', ['markup.deleted'], P['del']), rule('Diff changed', ['markup.changed'], P['mod']),
        rule('Invalid', ['invalid', 'invalid.illegal'], P['err']),
    ]


def semantic(P):
    return {'class': P['t'], 'type': P['t'], 'interface': P['t'], 'enum': P['t'], 'typeParameter': P['t'], 'function': P['f'], 'method': P['f'],
            'property': P['p'], 'parameter': P['p'], 'decorator': P['d'], 'namespace': P['t'], 'number': P['n'], 'string': P['s'],
            'variable.readonly': P['n'], 'enumMember': P['n'], 'selfParameter': P['p'], 'builtinConstant': P['n'],
            '*.deprecated': {'strikethrough': True}, **skript(P)}


# Minecraft colour codes (&0 to &f), lifted so every one stays readable on the dark editor; same hue family as in the game.
MC = {'0': '#6A6F80', '1': '#7474F2', '2': '#3CBF3C', '3': '#2CB8B8', '4': '#E24A4A', '5': '#C452C4', '6': '#FFAA00', '7': '#AAAAAA',
      '8': '#8E8E8E', '9': '#7B7BFF', 'a': '#55FF55', 'b': '#55FFFF', 'c': '#FF5555', 'd': '#FF55FF', 'e': '#FFFF55', 'f': '#FFFFFF'}


def skript(P):
    """Skript (PrimalMines) is coloured by the IntelliSkript extension's semantic tokens, not by TextMate scopes."""
    out = {'event': {'foreground': P['d'], 'bold': True},  # on join:, on death:  (Anemo, what sets things moving)
           'effect': P['f'],                                # send, set, give  (Geo, the actions)
           'expression': P['p'],                            # player's name, {_x}  (Cryo, values you read)
           'condition': P['k'],                             # if player has permission  (Electro, logic that steers)
           'pattern': P['d'], 'permission': {'foreground': P['s'], 'italic': True}}
    out.update({'*.bukkit_' + k: v for k, v in MC.items()})
    out.update({'*.bukkit_l': {'bold': True}, '*.bukkit_m': {'strikethrough': True}, '*.bukkit_n': {'underline': True}, '*.bukkit_o': {'italic': True}})
    return out


# Pick your element (his pick #5, 15 Oct: all seven): the accent (tabs, badges, buttons, cursor, active line number) takes one element.
ELEMENTS = [('Pyro', 'n'), ('Hydro', 't'), ('Anemo', 'd'), ('Electro', 'k'), ('Dendro', 's'), ('Cryo', 'p'), ('Geo', 'f')]


def mix(c1, c2, t):
    """Blend two #RRGGBB colours: t = 0 gives c1, t = 1 gives c2."""
    return '#' + ''.join('%02X' % round(int(c1[i:i + 2], 16) * (1 - t) + int(c2[i:i + 2], 16) * t) for i in (1, 3, 5))


def accented(P, name, e):
    return dict(P, label='%s · %s' % (P['label'], name), acc=P[e], acc2=mix(P[e], '#FFFFFF', .35))


def all_themes():
    """(file name, palette) for every theme: the two variants, then each with every element accent."""
    out = []
    for key, P in VARIANTS.items():
        out.append(('irminsul-%s-color-theme.json' % key, P))
        for name, e in ELEMENTS:
            out.append(('irminsul-%s-%s-color-theme.json' % (key, name.lower()), accented(P, name, e)))
    return out


def build():
    themes = all_themes()
    for fname, P in themes:
        theme = {'$schema': 'vscode://schemas/color-theme', 'name': P['label'], 'type': 'dark', 'semanticHighlighting': True,
                 'colors': colors(P), 'tokenColors': token_colors(P), 'semanticTokenColors': semantic(P)}
        (HERE / 'themes' / fname).write_text(json.dumps(theme, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    # keep package.json's theme list in step with the files
    pkg_path = HERE / 'package.json'
    pkg = json.loads(pkg_path.read_text(encoding='utf-8'))
    pkg['contributes']['themes'] = [{'label': P['label'], 'uiTheme': 'vs-dark', 'path': './themes/' + fname} for fname, P in themes]
    pkg_path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    # the same terminal palette as colour schemes for Windows Terminal (its "purple" is VS Code's "magenta")
    schemes = []
    for key, P in VARIANTS.items():
        A = P['ansi']
        sc = {'name': P['label'], 'background': P['term'], 'foreground': P['fg'], 'cursorColor': P['acc2'], 'selectionBackground': P['hl']}
        sc.update({{'magenta': 'purple', 'brightMagenta': 'brightPurple'}.get(k, k): v for k, v in A.items()})
        schemes.append(sc)
    (HERE / 'themes' / 'windows-terminal-schemes.json').write_text(json.dumps(schemes, indent=4) + '\n', encoding='utf-8')
    return ['%d themes written (%d interface colours, %d code rules each); package.json updated' %
            (len(themes), len(theme['colors']), len(theme['tokenColors']))]


if __name__ == '__main__':
    print('\n'.join(build()))
