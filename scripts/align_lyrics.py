"""Forced alignment van de EXACTE tekst op het zangspoor (Frans wav2vec2, Apache-2.0).
Gebruik: python3 -I align_lyrics.py <lead_vocal.wav> <tekst.txt> <whisper_words.json> <uit.json>
Werkt per tekstregel; het venster per regel komt uit de grove Whisper-tijden.
"""
import sys, re, json, unicodedata, difflib
import numpy as np, librosa, torch, torchaudio.functional as F
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

WAV, LYR, WJ, OUT = sys.argv[1:5]
MODEL = 'jonatasgrosman/wav2vec2-large-xlsr-53-french'
proc = Wav2Vec2Processor.from_pretrained(MODEL, cache_dir='models'); model = Wav2Vec2ForCTC.from_pretrained(MODEL, cache_dir='models').eval()
vocab = proc.tokenizer.get_vocab()
y, sr = librosa.load(WAV, sr=16000, mono=True)

def norm(w):
    w = unicodedata.normalize('NFD', w.lower()); w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return re.sub(r"[^a-z]", '', w)

raw = open(LYR, encoding='utf-8').read().replace('’', "'").replace('**', '')
lines = []
for ln in raw.splitlines():
    ln = re.sub(r'\([^)]*\)', ' ', ln).replace('…', ' ').strip()
    if ln and not ln.lower().startswith('lyrics'): lines.append(ln.split())
otoks = [(li, w) for li, ws in enumerate(lines) for w in ws]
words = json.load(open(WJ)); wt = [norm(w) for _, _, w in words]
sm = difflib.SequenceMatcher(a=[norm(w) for _, w in otoks], b=wt, autojunk=False)
tt = [None] * len(otoks)
for a, b, n in sm.get_matching_blocks():
    for k in range(n): tt[a + k] = (words[b + k][0], words[b + k][1])
known = [i for i, t in enumerate(tt) if t]
for i in range(len(tt)):
    if tt[i] is None:
        p = max([j for j in known if j < i], default=None); q = min([j for j in known if j > i], default=None)
        if p is not None and q is not None:
            t = tt[p][1] + (tt[q][0] - tt[p][1]) * (i - p) / (q - p + 1)
        elif p is not None: t = tt[p][1] + 0.5 * (i - p)
        else: t = max(0.0, tt[q][0] - 0.5 * (q - i))
        tt[i] = (t, t + 0.3)
line_start = {}; line_end = {}
for (li, w), (s, e) in zip(otoks, tt):
    line_start.setdefault(li, s); line_end[li] = e

def text_ids(ws):
    s = '|'.join(w.lower() for w in ws)
    s = s.replace('œ', 'œ')
    ids, chars = [], []
    for c in s:
        if c in vocab: ids.append(vocab[c]); chars.append(c)
    return ids, chars

out = []
nl = len(lines)
for li, ws in enumerate(lines):
    a = max(0.0, line_start[li] - 0.8)
    b = (line_start[li + 1] - 0.05) if li + 1 < nl else line_end[li] + 2.0
    b = max(b, line_end[li] + 0.6)
    seg = y[int(a * sr): int(b * sr)]
    ids, chars = text_ids(ws)
    if len(seg) < sr * 0.3 or not ids:
        continue
    with torch.no_grad():
        logits = model(torch.tensor(seg)[None].float()).logits
    lp = torch.log_softmax(logits, -1)
    T = lp.shape[1]
    if T < len(ids) * 2:  # te kort venster: overslaan
        continue
    ali, scores = F.forced_align(lp, torch.tensor([ids], dtype=torch.int32), blank=vocab['<pad>'])
    ali = ali[0].tolist(); sc = scores[0].exp().tolist()
    fdur = (len(seg) / sr) / T
    # tokens -> tijden
    spans = []; prev = vocab['<pad>']; k = -1
    for f, tkn in enumerate(ali):
        if tkn != vocab['<pad>'] and (tkn != prev or prev == vocab['<pad>']):
            k += 1; spans.append([k, f, f, sc[f]])
        elif tkn != vocab['<pad>'] and spans:
            spans[-1][2] = f
        prev = tkn
    ctimes = [(chars[s[0]], a + s[1] * fdur, a + (s[2] + 1) * fdur, s[3]) for s in spans if s[0] < len(chars)]
    # per woord
    wi = 0; cur = []
    wlist = []
    for c in ctimes:
        if c[0] == '|':
            if cur: wlist.append(cur); cur = []
        else: cur.append(c)
    if cur: wlist.append(cur)
    for w, cs in zip(ws, wlist):
        out.append({'line': li, 'word': w, 'start': round(cs[0][1], 3), 'end': round(cs[-1][2], 3),
                    'chars': [(c, round(s, 3), round(e, 3)) for c, s, e, _ in cs],
                    'conf': round(float(np.mean([x[3] for x in cs])), 3)})
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=0)
print('woorden uitgelijnd:', len(out), 'van', len(otoks), '| gem. zekerheid', round(np.mean([o['conf'] for o in out]), 3))
print(' '.join(f"{o['start']}:{o['word']}" for o in out[:30]))
