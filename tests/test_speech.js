// Tests for src/speech.js (no VS Code needed):  node tests/test_speech.js
// The reading test uses a stand-in Piper that writes *silent* sound files, played by the real hidden PowerShell player,
// so the whole path runs and nothing is heard.
'use strict';
const assert = require('assert');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { prepare, engineArgs, Reader } = require('../src/speech');

let passed = 0;
function check(name, fn) { fn(); passed++; console.log('  ok  ' + name); }

// ---------- prepare ----------
const md = [
  '# Irminsul status',
  '**Progress: 64%** `█████░░░`',
  '- [ ] Go over real files together ← recommended',
  'Preview `docs/preview.html` is done. Version 3.5 is next!',
  '```py',
  "print('never read')",
  '```',
  '---',
  'See [the page](https://claude.ai/artifact/abc) after code.'
].join('\n');
const mp = prepare(md, 'markdown');
check('markdown: headings, bold, checkboxes and arrows are not spoken', () => {
  assert.deepStrictEqual(mp.map((p) => p.text), [
    'Irminsul status', 'Progress: 64%', 'Go over real files together recommended',
    'Preview docs/preview.html is done.', 'Version 3.5 is next!', 'See the page after code.']);
});
check('markdown: a dot inside a word or number does not cut the sentence', () => {
  assert.ok(mp.some((p) => p.text.startsWith('Preview docs/preview.html')));
});
check('markdown: fenced code and --- lines are skipped', () => {
  assert.ok(!mp.some((p) => /never read|---/.test(p.text)));
});
check('markdown: each sentence points at its own words in the file', () => {
  const p = mp.find((x) => x.text.startsWith('Version'));
  assert.strictEqual(md.slice(p.start, p.end), 'Version 3.5 is next!');
  const q = mp.find((x) => x.text.startsWith('Preview'));
  assert.strictEqual(md.slice(q.start, q.end), 'Preview `docs/preview.html` is done.');
});
const code = 'def safety_copy(self, force=False):\n    return {"ok": True}  # done';
check('code: punctuation is dropped, snake_case becomes words', () => {
  const t = prepare(code, 'python').map((p) => p.text);
  assert.strictEqual(t[0], 'def safety copy self, force False:');
  assert.ok(!/[(){}"=]/.test(t.join(' ')));
});
check('plain text is read as written', () => {
  assert.deepStrictEqual(prepare('Hello there. (Really) yes', 'plaintext').map((p) => p.text), ['Hello there.', '(Really) yes']);
});
check('engine command lines: Kokoro gets the speed, Piper gets a length scale', () => {
  const k = engineArgs({ engine: 'kokoro', worker: 'w.py', model: 'm', voicesFile: 'v', voice: 'af_sky', speed: 1.1, tmpDir: 't' });
  assert.deepStrictEqual(k, ['-I', 'w.py', '--model', 'm', '--voices', 'v', '--voice', 'af_sky', '--speed', '1.10', '--output_dir', 't']);
  const p = engineArgs({ engine: 'piper', model: 'm', speed: 2, tmpDir: 't' });
  assert.strictEqual(p[p.indexOf('--length_scale') + 1], '0.50');
});
check('nothing to say gives no pieces', () => {
  assert.strictEqual(prepare('---\n***\n\n', 'markdown').length, 0);
});

// ---------- Reader, with a stand-in Piper and the real silent player ----------
const FAKE_PIPER = `
const fs = require('fs'), path = require('path'), rl = require('readline');
const dir = process.argv[process.argv.indexOf('--output_dir') + 1];
const n = 2205, wav = Buffer.alloc(44 + n * 2);  // 0.1 s of silence, 22050 Hz, 16-bit mono
wav.write('RIFF', 0); wav.writeUInt32LE(36 + n * 2, 4); wav.write('WAVEfmt ', 8); wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20);
wav.writeUInt16LE(1, 22); wav.writeUInt32LE(22050, 24); wav.writeUInt32LE(44100, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
wav.write('data', 36); wav.writeUInt32LE(n * 2, 40);
let i = 0;
const mode = process.env.FAKE_MODE || 'stdout';  // where the path is printed; real Piper printed it on stderr (28 Oct)
console.error('[2026-10-28 12:12:46.736] [piper] [info] Loaded voice in 0.22 second(s)');
rl.createInterface({ input: process.stdin }).on('line', (l) => {
  const f = path.join(dir, 'fake' + (i++) + '.wav'); fs.writeFileSync(f, wav);
  if (mode !== 'stderr') console.log(f);
  if (mode !== 'stdout') { console.error(f); console.error('[piper] [info] Real-time factor: 0.04'); }
});
`;
function makeReader(tmp, mode) {
  return new Reader({ engine: 'piper', exe: 'unused', model: 'unused', tmpDir: tmp,
    spawnEngine: (args) => spawn(process.execPath, ['-e', FAKE_PIPER, '--', ...args],
      { windowsHide: true, env: Object.assign({}, process.env, { FAKE_MODE: mode || 'stdout' }) }) });
}
function playsInOrder(tmp, mode, ok, fail) {
  const r = makeReader(tmp, mode), seen = [];
  r.on('piece', (i) => seen.push(i));
  r.on('error', (m) => fail(new Error(m)));
  r.on('done', () => { try { assert.deepStrictEqual(seen, [0, 1, 2]); ok(); } catch (e) { fail(e); } });
  r.start(prepare('One. Two. Three.', 'plaintext'));
}
function run(name, fn) { return new Promise((res, rej) => { const t = setTimeout(() => rej(new Error(name + ': timed out')), 60000); fn(() => { clearTimeout(t); passed++; console.log('  ok  ' + name); res(); }, rej); }); }

(async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'irminsul-test-'));
  await run('reading: every sentence plays in order, then done, files tidied', (ok, fail) => {
    const r = makeReader(tmp), seen = [];
    r.on('piece', (i) => seen.push(i));
    r.on('error', (m) => fail(new Error(m)));
    r.on('done', () => {
      try {
        assert.deepStrictEqual(seen, [0, 1, 2]);
        assert.strictEqual(fs.readdirSync(tmp).filter((f) => f.endsWith('.wav')).length, 0);
        ok();
      } catch (e) { fail(e); }
    });
    r.start(prepare('One. Two. Three.', 'plaintext'));
  });
  await run('reading: works when Piper prints the file name on stderr, like it did on his PC', (ok, fail) => playsInOrder(tmp, 'stderr', ok, fail));
  await run('reading: a file name printed on both streams plays only once', (ok, fail) => playsInOrder(tmp, 'both', ok, fail));
  await run('reading: Stop in the middle ends it once and stops both helpers', (ok, fail) => {
    const r = makeReader(tmp);
    let dones = 0;
    r.on('piece', (i) => { if (i === 0) r.stop(); });
    r.on('done', () => {
      dones++;
      setTimeout(() => {
        try {
          assert.strictEqual(dones, 1);
          assert.ok(r.piper.killed || r.piper.exitCode !== null);
          assert.ok(r.player.killed || r.player.exitCode !== null);
          ok();
        } catch (e) { fail(e); }
      }, 300);
    });
    r.start(prepare('A. B. C. D. E. F.', 'plaintext'));
  });
  await run('reading: a missing Piper gives a clear error, not a hang', (ok, fail) => {
    const r = new Reader({ engine: 'piper', name: 'Piper', exe: path.join(tmp, 'no-such-piper.exe'), model: 'x', tmpDir: tmp });
    let msg = '';
    r.on('error', (m) => { msg = m; });
    r.on('done', () => { try { assert.match(msg, /Piper could not start/); ok(); } catch (e) { fail(e); } });
    r.start(prepare('Hello.', 'plaintext'));
  });
  // the real Kokoro helper with the real Sky voice, but a silent stand-in player (nothing is heard)
  const K = path.join(process.env.LOCALAPPDATA || '', 'Irminsul', 'kokoro');
  const py = path.join(K, 'venv', 'Scripts', 'python.exe');
  if (fs.existsSync(py)) {
    await run('Kokoro Sky: the real helper makes every sentence, in order', (ok, fail) => {
      const quiet = spawn(process.execPath, ['-e', "require('readline').createInterface({input:process.stdin}).on('line',l=>{const i=l.split('|')[0];" +
        "const f=l.slice(i.length+1);const ok=require('fs').readFileSync(f).slice(0,4).toString()==='RIFF';console.log('start '+i);console.log(ok?'end '+i:'error '+i+' not a WAV')})"],
        { windowsHide: true });
      const r = new Reader({ engine: 'kokoro', name: 'Kokoro', exe: py, worker: path.join(__dirname, '..', 'src', 'kokoro_worker.py'),
        model: path.join(K, 'kokoro-v1.0.onnx'), voicesFile: path.join(K, 'voices-v1.0.bin'), voice: 'af_sky', speed: 1.1, tmpDir: tmp, player: quiet });
      const seen = [];
      r.on('piece', (i) => seen.push(i));
      r.on('error', (m) => fail(new Error(m)));
      r.on('done', () => { try { assert.deepStrictEqual(seen, [0, 1, 2]); ok(); } catch (e) { fail(e); } });
      r.start(prepare('# Irminsul\nThe world tree holds all knowledge. Tonight, it reads aloud.', 'markdown'));
    });
  } else {
    console.log('  --  Kokoro is not installed here, its real test is skipped');
  }
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('speech tests passed (' + passed + ' checks)');
})().catch((e) => { console.error('FAIL ' + e.message); process.exit(1); });
