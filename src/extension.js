// Irminsul read aloud (28 Oct 2026): reads the selection, or the whole file, with a Piper voice; the sentence being read glows gold.
// Commands: Irminsul: Read aloud, Irminsul: Stop reading, and Ctrl+Alt+R to start or stop. Settings under "Irminsul" (voice, speed).
'use strict';
const vscode = require('vscode');
const os = require('os');
const path = require('path');
const fs = require('fs');
const { prepare, Reader } = require('./speech');

// Sky (Kokoro) is the default voice; Kokoro has no Dutch, so Dutch reads with Piper's Nathalie. Lessac is the first Piper voice.
const VOICES = {
  sky: { engine: 'kokoro', name: 'Kokoro', voice: 'af_sky' },
  dutch: { engine: 'piper', name: 'Piper', model: 'nl_BE-nathalie-medium' },
  lessac: { engine: 'piper', name: 'Piper', model: 'en_US-lessac-medium' }
};

let reader = null, status = null, glow = null;

function baseFolder() {
  const set = vscode.workspace.getConfiguration('irminsul.readAloud').get('folder');
  return set || path.join(process.env.LOCALAPPDATA || os.homedir(), 'Irminsul');
}

/** Everything the reader needs for one voice, plus the files that must exist: [path, what it is]. */
function voiceSetup(key, folder) {
  const v = VOICES[key] || VOICES.sky;
  if (v.engine === 'kokoro') {
    const k = path.join(folder, 'kokoro');
    const o = { engine: 'kokoro', name: v.name, voice: v.voice, exe: path.join(k, 'venv', 'Scripts', 'python.exe'),
      worker: path.join(__dirname, 'kokoro_worker.py'), model: path.join(k, 'kokoro-v1.0.onnx'), voicesFile: path.join(k, 'voices-v1.0.bin') };
    return { o, need: [[o.exe, 'Kokoro'], [o.model, 'the Kokoro voice model'], [o.voicesFile, 'the Kokoro voices']] };
  }
  const o = { engine: 'piper', name: v.name, exe: path.join(folder, 'piper', 'piper', 'piper.exe'),
    model: path.join(folder, 'piper', 'voices', v.model + '.onnx') };
  return { o, need: [[o.exe, 'Piper'], [o.model, 'the voice']] };
}

function setReading(on) {
  vscode.commands.executeCommand('setContext', 'irminsul.reading', on);
  status.text = on ? '$(debug-stop) Reading' : '$(unmute)';
  status.tooltip = on ? 'Stop reading (Ctrl+Alt+R or Esc)' : 'Read aloud: the selection, or the whole file (Ctrl+Alt+R)';
  status.command = on ? 'irminsul.stopReading' : 'irminsul.readAloud';
}

function stop() {
  if (reader) { const r = reader; reader = null; r.stop(); }
}

function readAloud() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) { vscode.window.showInformationMessage('Open a file first, then choose Read aloud.'); return; }
  stop();
  const cfg = vscode.workspace.getConfiguration('irminsul.readAloud');
  const doc = editor.document, sel = editor.selection;
  const range = sel.isEmpty ? new vscode.Range(0, 0, doc.lineCount, 0) : sel;
  const base = doc.offsetAt(range.start);
  const pieces = prepare(doc.getText(range), doc.languageId).map((p) => Object.assign(p, { start: base + p.start, end: base + p.end }));
  if (!pieces.length) { vscode.window.showInformationMessage('There are no words to read here.'); return; }

  const { o, need } = voiceSetup(cfg.get('voice'), baseFolder());
  for (const [f, what] of need) {
    if (!fs.existsSync(f)) { vscode.window.showErrorMessage('Read aloud needs ' + what + ', which is not at ' + f + '. Set its folder in Settings → Irminsul.'); return; }
  }

  const version = doc.version, follow = cfg.get('highlight');
  const r = new Reader(Object.assign(o, { speed: cfg.get('speed'), tmpDir: path.join(os.tmpdir(), 'irminsul-read-aloud') }));
  reader = r;
  r.on('piece', (i) => {
    if (reader !== r || !follow || doc.version !== version) return;  // the file changed: stop following, keep reading
    const p = pieces[i], rg = new vscode.Range(doc.positionAt(p.start), doc.positionAt(p.end));
    for (const ed of vscode.window.visibleTextEditors) {
      if (ed.document !== doc) continue;
      ed.setDecorations(glow, [rg]);
      ed.revealRange(rg, vscode.TextEditorRevealType.InCenterIfOutsideViewport);
    }
  });
  r.on('error', (msg) => vscode.window.showErrorMessage('Read aloud: ' + msg));
  r.on('done', () => {
    for (const ed of vscode.window.visibleTextEditors) ed.setDecorations(glow, []);
    if (reader === r) reader = null;
    if (!reader) setReading(false);
  });
  setReading(true);
  r.start(pieces);
}

function activate(context) {
  glow = vscode.window.createTextEditorDecorationType({
    backgroundColor: 'rgba(243, 215, 156, 0.16)', border: '1px solid rgba(243, 215, 156, 0.45)', borderRadius: '3px',
    overviewRulerColor: 'rgba(243, 215, 156, 0.8)', overviewRulerLane: vscode.OverviewRulerLane.Center
  });
  status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  setReading(false);
  status.show();
  context.subscriptions.push(glow, status,
    vscode.commands.registerCommand('irminsul.readAloud', readAloud),
    vscode.commands.registerCommand('irminsul.stopReading', stop),
    vscode.commands.registerCommand('irminsul.toggleReading', () => (reader ? stop() : readAloud())),
    vscode.workspace.onDidCloseTextDocument(() => { if (reader && !vscode.window.activeTextEditor) stop(); }),
    { dispose: stop });
}

function deactivate() { stop(); }

module.exports = { activate, deactivate };
