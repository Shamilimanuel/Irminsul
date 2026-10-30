// Wiring test for src/extension.js with a stand-in VS Code and a stand-in reader:  node tests/test_extension.js
// Checks the commands exist, the gold highlight follows the sentence being read, and the button flips to Stop and back.
'use strict';
const assert = require('assert');
const Module = require('module');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { EventEmitter } = require('events');

// a fake voices folder, so the "are the voice files there?" check passes without running anything
const piper = fs.mkdtempSync(path.join(os.tmpdir(), 'irminsul-voices-'));
fs.mkdirSync(path.join(piper, 'kokoro', 'venv', 'Scripts'), { recursive: true });
for (const f of [['kokoro', 'venv', 'Scripts', 'python.exe'], ['kokoro', 'kokoro-v1.0.onnx'], ['kokoro', 'voices-v1.0.bin']]) fs.writeFileSync(path.join(piper, ...f), '');

const text = '# Title\nFirst sentence. Second one!\n';
class Pos { constructor(o) { this.o = o; } }
class Range { constructor(a, b, c, d) { this.a = typeof a === 'number' ? a : a; this.args = [a, b, c, d]; } }
const doc = { version: 1, languageId: 'markdown', lineCount: 3, getText: () => text, offsetAt: () => 0, positionAt: (o) => new Pos(o) };
const decorations = [], contexts = [], commands = {}, messages = [];
const editor = { document: doc, selection: { isEmpty: true }, setDecorations: (t, r) => decorations.push(r.map((x) => [x.args[0].o, x.args[1].o])), revealRange: () => {} };
const status = { show() {}, text: '', tooltip: '', command: '' };
const vscode = {
  window: { activeTextEditor: editor, visibleTextEditors: [editor], createTextEditorDecorationType: () => ({ dispose() {} }),
    createStatusBarItem: () => status, showInformationMessage: (m) => messages.push(m), showErrorMessage: (m) => messages.push(m) },
  workspace: { getConfiguration: () => ({ get: (k) => ({ folder: piper, voice: 'sky', speed: 1.1, highlight: true })[k] }),
    onDidCloseTextDocument: () => ({ dispose() {} }) },
  commands: { registerCommand: (n, f) => { commands[n] = f; return { dispose() {} }; }, executeCommand: (c, k, v) => contexts.push(v) },
  Range, StatusBarAlignment: { Right: 2 }, OverviewRulerLane: { Center: 2 }, TextEditorRevealType: { InCenterIfOutsideViewport: 2 }
};

let lastReader = null;
class FakeReader extends EventEmitter {
  constructor(o) { super(); this.o = o; lastReader = this; }
  start(pieces) { this.pieces = pieces; }
  stop() { this.emit('done'); }
}
const realLoad = Module._load;
Module._load = function (req, parent, isMain) {
  if (req === 'vscode') return vscode;
  const m = realLoad.apply(this, arguments);
  return req === './speech' ? Object.assign({}, m, { Reader: FakeReader }) : m;
};

const ext = require('../src/extension');
ext.activate({ subscriptions: [] });
assert.ok(commands['irminsul.readAloud'] && commands['irminsul.stopReading'] && commands['irminsul.toggleReading'], 'commands registered');
assert.strictEqual(status.text, '$(unmute)');
console.log('  ok  commands and the button exist');

commands['irminsul.toggleReading']();
assert.ok(lastReader, 'a reader started');
assert.deepStrictEqual(lastReader.pieces.map((p) => p.text), ['Title', 'First sentence.', 'Second one!']);
assert.strictEqual(status.text, '$(debug-stop) Reading');
assert.strictEqual(contexts[contexts.length - 1], true);
assert.strictEqual(lastReader.o.engine, 'kokoro');
assert.strictEqual(lastReader.o.voice, 'af_sky');
assert.strictEqual(lastReader.o.speed, 1.1);
assert.ok(lastReader.o.model.endsWith('kokoro-v1.0.onnx') && lastReader.o.worker.endsWith('kokoro_worker.py'));
assert.ok(fs.existsSync(lastReader.o.worker), 'the Kokoro helper ships next to extension.js');
console.log('  ok  Ctrl+Alt+R starts reading the whole file with Kokoro Sky');

lastReader.emit('piece', 1);
assert.deepStrictEqual(decorations[decorations.length - 1], [[8, 23]]);
assert.strictEqual(text.slice(8, 23), 'First sentence.');
console.log('  ok  the gold highlight sits on the sentence being read');

commands['irminsul.toggleReading']();
assert.deepStrictEqual(decorations[decorations.length - 1], [], 'highlight cleared');
assert.strictEqual(status.text, '$(unmute)');
assert.strictEqual(contexts[contexts.length - 1], false);
console.log('  ok  pressing it again stops, clears the highlight and flips the button back');

fs.rmSync(piper, { recursive: true, force: true });
assert.strictEqual(messages.length, 0, 'no error messages: ' + messages.join(' | '));
console.log('extension tests passed (4 checks)');
