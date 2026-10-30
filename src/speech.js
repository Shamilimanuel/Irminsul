// Irminsul read-aloud engine (28 Oct 2026). No VS Code in here, so it can be tested with plain Node (tests/test_speech.js).
// prepare() cuts text into sentences that remember where they sit in the file; Reader speaks them with one voice program for the
// whole read (Kokoro or Piper; the voice loads once), and plays each finished sentence through a hidden PowerShell sound player.
'use strict';
const { spawn } = require('child_process');
const { EventEmitter } = require('events');
const fs = require('fs');
const path = require('path');

// ---------- turning text into speakable sentences ----------

const MARKDOWN = new Set(['markdown', 'md']);
const PLAIN = new Set(['plaintext', 'text', 'log']);

/** What a human would say for one Markdown line: no #, **, `, [ ], link addresses or progress bars. */
function cleanMarkdown(s) {
  return s
    .replace(/^\s{0,3}#{1,6}\s+/, '')                 // heading marks
    .replace(/^\s*>\s?/, '')                          // quotes
    .replace(/^\s*(?:[-*+]|\d+[.)])\s+/, '')          // list markers
    .replace(/^\s*\[[ xX]\]\s+/, '')                  // checkboxes
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')         // images: keep the alt text
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')          // links: keep the words
    .replace(/<[^>]+>/g, ' ')                         // html tags
    .replace(/https?:\/\/\S+/g, 'a link')
    .replace(/(\*\*|__|\*|_|`|~~)/g, '')              // bold, italic, code, strike
    .replace(/[█░▓▒■□←→↑↓|]+/g, ' ')                  // bars, arrows, table pipes
    .replace(/<!--.*?-->/g, ' ');
}

/** Code read aloud: words stay, the punctuation noise goes, snake_case becomes words. */
function cleanCode(s) {
  return s.replace(/https?:\/\/\S+/g, 'a link').replace(/[_]/g, ' ').replace(/[{}[\]()<>;=+*/\\|&^%$#@~`"'!]+/g, ' ');
}

/**
 * Cut text into pieces to speak. Each piece: { text (what is said), start, end (offsets into `text` as given) }.
 * Lines are always a break; inside a line, a sentence ends at . ! or ? followed by a space.
 */
function prepare(text, languageId) {
  const md = MARKDOWN.has(languageId), plain = PLAIN.has(languageId);
  let src = text;
  if (md) {  // fenced code blocks are not read; blank them out but keep every offset where it was
    src = src.replace(/^(\s*)(```|~~~)[^]*?^\s*\2[^\n]*$/gm, (m) => m.replace(/[^\n]/g, ' '));
  }
  const pieces = [];
  const lineRx = /[^\n]+/g;
  let m;
  while ((m = lineRx.exec(src))) {
    const line = m[0], lineStart = m.index;
    // a sentence ends at . ! ? followed by a space or the end of the line, so "status.md" and "3.5" stay whole
    const cuts = [], ends = /[.!?]+(?=\s|$)/g;
    let from = 0, e;
    while ((e = ends.exec(line))) { cuts.push([from, e.index + e[0].length]); from = e.index + e[0].length; }
    if (from < line.length) cuts.push([from, line.length]);
    for (const [a, b] of cuts) {
      const raw = line.slice(a, b);
      const lead = raw.length - raw.trimStart().length, trail = raw.length - raw.trimEnd().length;
      const start = lineStart + a + lead, end = lineStart + b - trail;
      if (end <= start) continue;
      let said = text.slice(start, end);
      said = md ? cleanMarkdown(said) : plain ? said : cleanCode(said);
      said = said.replace(/\s+/g, ' ').replace(/\s+([,.:;!?])/g, '$1').trim();
      if (!/[\p{L}\p{N}]/u.test(said)) continue;  // nothing worth saying (only symbols)
      pieces.push({ text: said, start, end });
    }
  }
  return pieces;
}

// ---------- speaking ----------

// The hidden player: reads "index|file.wav" lines, says "start i" and "end i" around playing each one, then deletes the file.
const PLAYER_PS = [
  '$p = New-Object System.Media.SoundPlayer',
  'while ($null -ne ($l = [Console]::In.ReadLine())) {',
  '  $i, $f = $l -split "\\|", 2',
  '  [Console]::Out.WriteLine("start $i"); [Console]::Out.Flush()',
  '  try { $p.SoundLocation = $f; $p.PlaySync() } catch { [Console]::Out.WriteLine("error $i $($_.Exception.Message)") }',
  '  Remove-Item -LiteralPath $f -ErrorAction SilentlyContinue',
  '  [Console]::Out.WriteLine("end $i"); [Console]::Out.Flush()',
  '}'
].join('\n');

function lines(stream, onLine) {
  let buf = '';
  stream.setEncoding('utf8');
  stream.on('data', (d) => {
    buf += d;
    let i;
    while ((i = buf.indexOf('\n')) >= 0) { const l = buf.slice(0, i).trim(); buf = buf.slice(i + 1); if (l) onLine(l); }
  });
}

/**
 * The command line for a voice program. Both work the same way: one sentence per line in, the path of each WAV file out.
 * engine 'kokoro': exe = Kokoro's Python, plus worker, model, voicesFile, voice (e.g. af_sky); speed goes straight in.
 * engine 'piper': exe = piper.exe, plus model; Piper takes speed as a length scale (2 = twice as slow).
 */
function engineArgs(o) {
  const speed = Math.min(2, Math.max(0.5, o.speed || 1));
  if (o.engine === 'kokoro') {
    return ['-I', o.worker, '--model', o.model, '--voices', o.voicesFile, '--voice', o.voice, '--speed', speed.toFixed(2),
      '--output_dir', o.tmpDir];
  }
  return ['--model', o.model, '--output_dir', o.tmpDir, '--length_scale', (1 / speed).toFixed(2), '--sentence_silence', '0.15'];
}

/**
 * Reader: speaks pieces in order. Events: 'piece' (index) as it starts playing, 'done' when all are spoken or stopped,
 * 'error' (message). options: engine ('kokoro' or 'piper'), name (for messages), exe and the engine's files (see engineArgs),
 * speed (1 = normal), tmpDir, player and spawnEngine (optional: stand-ins for tests).
 */
class Reader extends EventEmitter {
  constructor(options) {
    super();
    this.o = Object.assign({ speed: 1 }, options);
    this.stopped = false;
  }

  start(pieces) {
    const o = this.o;
    this.pieces = pieces;
    fs.mkdirSync(o.tmpDir, { recursive: true });
    const args = engineArgs(o);
    this.piper = o.spawnEngine ? o.spawnEngine(args)  // tests swap in a stand-in voice program
      : spawn(o.exe, args, { cwd: path.dirname(o.exe), windowsHide: true });
    this.player = o.player || spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand',
      Buffer.from(PLAYER_PS, 'utf16le').toString('base64')], { windowsHide: true });

    // Piper prints the path of each finished file, in the order the lines went in. On his PC it printed the path on stderr
    // (28 Oct, between its [info] log lines), so both streams are read; a path is only queued once.
    let made = 0, ended = 0, err = '';
    const queued = new Set();
    const onLine = (l) => {
      if (!/\.wav$/i.test(l) || l.startsWith('[') || queued.has(l) || this.stopped) return;
      queued.add(l);
      this.player.stdin.write(made++ + '|' + l + '\n');
    };
    lines(this.piper.stdout, onLine);
    lines(this.piper.stderr, (l) => { err = (err + '\n' + l).slice(-2000); onLine(l); });
    const name = o.name || 'The voice';
    this.piper.on('error', (e) => this.fail(name + ' could not start: ' + e.message));
    this.piper.on('exit', (code) => { if (code && !this.stopped) this.fail(name + ' stopped (code ' + code + '): ' + err.trim().split('\n').pop()); });
    lines(this.player.stdout, (l) => {
      const [what, idx] = l.split(' ');
      if (what === 'start') this.emit('piece', Number(idx));
      else if (what === 'error') this.emit('error', 'Could not play a sentence: ' + l.split(' ').slice(2).join(' '));
      else if (what === 'end' && ++ended === pieces.length) this.finish();
    });
    this.player.on('error', (e) => this.fail('The sound player could not start: ' + e.message));

    for (const p of pieces) this.piper.stdin.write(p.text.replace(/[\r\n]+/g, ' ') + '\n');
    this.piper.stdin.end();
  }

  fail(msg) { if (this.stopped) return; this.emit('error', msg); this.stop(); }

  finish() { if (this.stopped) return; this.stop(); }

  stop() {
    if (this.stopped) return;
    this.stopped = true;
    for (const c of [this.piper, this.player]) { try { if (c && c.kill) c.kill(); } catch (e) { /* already gone */ } }
    try { for (const f of fs.readdirSync(this.o.tmpDir)) if (/\.wav$/i.test(f)) fs.unlinkSync(path.join(this.o.tmpDir, f)); } catch (e) { /* nothing to tidy */ }
    this.emit('done');
  }
}

module.exports = { prepare, cleanMarkdown, cleanCode, engineArgs, Reader };
