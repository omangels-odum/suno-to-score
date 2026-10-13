"""Bouwt de master-partituur v0.1 van een Suno-stuk uit de Advanced-split-MIDI (gedeelde tempokaart).
Gebruik: python3 -I build_master.py <map-met-suno-mid> <words.json> <lyrics.txt> <percussie.wav|-> <uitvoermap>
Conventie: 1 Suno-tel = achtste noot (Suno exporteert rond 125-155 BPM; muzikaal is het stuk ca. 61-78 per kwartnoot).
"""
import sys, os, re, json, difflib, unicodedata, glob
import mido.midifiles.meta as mm
_o = mm.MetaSpec_key_signature.decode
def _safe(self, msg, data):
    try: _o(self, msg, data)
    except Exception: msg.key = 'C'
mm.MetaSpec_key_signature.decode = _safe
import pretty_midi as pm, numpy as np, music21 as m

SRC, WORDS, LYR, PERC, OUT = sys.argv[1:6]
os.makedirs(os.path.join(OUT,'partijen'), exist_ok=True)
Q = 0.25            # raster in kwartnoten (zestiende)
BAR = 4.0           # 4/4
def fn(stem): return glob.glob(os.path.join(SRC, f'*({stem}).mid'))[0]

ref = pm.PrettyMIDI(fn('Lead Vocal'))
TPB = ref.resolution
def t2q(sec):       # seconden -> kwartnoot-positie
    return ref.time_to_tick(sec) / TPB * 0.5
def qz(x): return round(x / Q) * Q

def notes_of(stem, minvel=1):
    p = pm.PrettyMIDI(fn(stem))
    out = []
    for ins in p.instruments:
        for n in ins.notes:
            s, e = qz(t2q(n.start)), qz(t2q(n.end))
            if e - s < Q: e = s + Q
            if n.velocity >= minvel: out.append([s, e, n.pitch, n.start])
    return sorted(out)

def monophonic(ns, prefer='high'):
    by = {}
    for s, e, p, sec in ns:
        if s not in by or (p > by[s][2] if prefer == 'high' else p < by[s][2]): by[s] = [s, e, p, sec]
    seq = [by[k] for k in sorted(by)]
    for a, b in zip(seq, seq[1:]):
        if a[1] > b[0]: a[1] = b[0]
    return [x for x in seq if x[1] - x[0] >= Q]

# ---------- zang ----------
lead = monophonic(notes_of('Lead Vocal'))
harm = notes_of('Backing Vocals') + notes_of('Choir')
# frasen: rust >= 1 kwartnoot
phrases, cur = [], [lead[0]]
for a, b in zip(lead, lead[1:]):
    if b[0] - a[1] >= 1.0: phrases.append(cur); cur = []
    cur.append(b)
phrases.append(cur)
voices = {'S1': [], 'S2': [], 'A': []}
mel_voice_at = []   # (start, end, voice)
for ph in phrases:
    v = 'A' if np.median([n[2] for n in ph]) < 63 else 'S1'
    voices[v] += [list(n) for n in ph]
    mel_voice_at.append((ph[0][0], ph[-1][1], v))
def mel_voice(t):
    for s, e, v in mel_voice_at:
        if s <= t < e: return v
    return None
mel_pitch = {n[0]: n[2] for n in lead}
slices = {}
for s, e, p, sec in harm:
    slices.setdefault(s, {})
    slices[s][p] = max(slices[s].get(p, 0), e)
for s in sorted(slices):
    mv = mel_voice(s)
    ps = sorted([p for p in slices[s] if p != mel_pitch.get(s)], reverse=True)[:3]
    if not ps: continue
    if mv == 'S1':   targets = ['S2', 'A']
    elif mv == 'A':  targets = ['S1', 'S2']
    else:            targets = ['S1', 'S2', 'A'][-len(ps):] if len(ps) > 1 else (['S2'] if ps[0] >= 62 else ['A'])
    for v, p in zip(targets, ps):
        voices[v].append([s, slices[s][p], p, None])
for v in voices: voices[v] = monophonic(voices[v])

# ---------- tekst ----------
def norm(w):
    w = unicodedata.normalize('NFD', w.lower()); w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return re.sub(r"[^a-z]", '', w)
raw = open(LYR, encoding='utf-8').read()
raw = re.sub(r'\([^)]*\)', ' ', raw).replace('**', ' ').replace('…', ' ').replace('’', "'")
raw = re.sub(r'^\s*Lyrics:\s*', '', raw)
otoks = [w for w in re.split(r"\s+", raw) if norm(w)]
words = json.load(open(WORDS))
wtoks = [norm(w) for _, _, w in words]
sm = difflib.SequenceMatcher(a=[norm(w) for w in otoks], b=wtoks, autojunk=False)
otime = [None] * len(otoks)
for a, b, size in sm.get_matching_blocks():
    for k in range(size): otime[a + k] = words[b + k][0]
# interpoleer ontbrekende tijden
idx = [i for i, t in enumerate(otime) if t is not None]
for i in range(len(otime)):
    if otime[i] is None:
        prev = max([j for j in idx if j < i], default=None); nxt = min([j for j in idx if j > i], default=None)
        if prev is not None and nxt is not None:
            otime[i] = otime[prev] + (otime[nxt] - otime[prev]) * (i - prev) / (nxt - prev)
        else: otime[i] = otime[prev] + 0.4 * (i - prev) if prev is not None else 0
VOW = 'aeiouyàâäéèêëîïôöûùüœæ'
def syllables(w):
    core = w.strip(".,;:!?")
    groups = re.findall(rf"[^{VOW}]*[{VOW}]+(?:[^{VOW}]*$)?", core, flags=re.I)
    if not groups: return [core]
    # medeklinkers tussen klinkergroepen: één naar de volgende lettergreep
    out, rest = [], core
    parts = re.split(rf"([{VOW}]+)", core, flags=re.I)
    syl, i = '', 0
    toks = [p for p in parts if p != '']
    res = []; buf = ''
    for t in toks:
        if re.fullmatch(rf"[{VOW}]+", t, flags=re.I): buf += t; res.append(buf); buf = ''
        else:
            if res and len(t) > 1: res[-1] += t[:-1]; buf = t[-1]
            elif res and len(t) == 1: buf = t
            else: buf = t
    if buf:
        if res: res[-1] += buf
        else: res = [buf]
    # stomme e op het einde niet apart als er een vorige lettergreep is
    if len(res) > 1 and re.fullmatch(r"[^aeiouy]*e[s]?|[^aeiouy]*ent", res[-1], flags=re.I) and not res[-1].lower().endswith(('é', 'è')):
        res = res[:-1] + [res[-1]]  # behouden: in zang wordt de stomme e vaak gezongen
    return res
lyr_on = {}   # (voice, start) -> tekst
allmel = sorted([(n[0], n[3], v) for v in voices for n in voices[v] if n[3] is not None])
for i, w in enumerate(otoks):
    t0 = otime[i] - 0.15; t1 = (otime[i + 1] - 0.15) if i + 1 < len(otoks) else 1e9
    cand = [x for x in allmel if t0 <= x[1] < t1 and (x[2], x[0]) not in lyr_on]
    syl = syllables(w)
    if not cand:
        later = [x for x in allmel if x[1] >= t0 and (x[2], x[0]) not in lyr_on][:1]
        cand = later
    if not cand: continue
    if len(syl) > len(cand): syl = syl[:len(cand) - 1] + [''.join(syl[len(cand) - 1:])]
    for k, s in enumerate(syl):
        key = (cand[k][2], cand[k][0])
        txt = s + ('-' if k < len(syl) - 1 else '')
        lyr_on[key] = txt
# homoritmische harmoniestemmen krijgen dezelfde tekst
melkeys = {s: t for (v, s), t in lyr_on.items()}
for v in voices:
    for n in voices[v]:
        if (v, n[0]) not in lyr_on and n[0] in melkeys: lyr_on[(v, n[0])] = melkeys[n[0]]

# ---------- piano ----------
pn = [n for n in notes_of('Piano', minvel=20)]
def chords(ns, maxn=4):
    by = {}
    for s, e, p, _ in ns: by.setdefault(s, []).append((p, e))
    keys = sorted(by); out = []
    for i, s in enumerate(keys):
        ps = sorted(set(p for p, _ in by[s]))
        if len(ps) > maxn: ps = [ps[0]] + ps[-(maxn - 1):]
        e = max(e for _, e in by[s])
        if i + 1 < len(keys): e = min(e, keys[i + 1])
        if e - s >= Q: out.append([s, e, ps])
    return out
rh = chords([n for n in pn if n[2] >= 60]); lh = chords([n for n in pn if n[2] < 60])

# ---------- strijkers ----------
st = notes_of('String Section', minvel=15)
vn = monophonic([n for n in st if n[2] >= 55], 'high')
vc_src = monophonic(st, 'low')
vc = []
for s, e, p, sec in vc_src:
    while p > 69: p -= 12
    while p < 36: p += 12
    vc.append([s, e, p, sec])

# ---------- harp: gebroken akkoord per maat uit de pianoharmonie ----------
end_q = max(n[1] for n in pn + lead)
nbars = int(np.ceil(end_q / BAR))
harp = []; pedals = []
for b in range(nbars):
    s0, s1 = b * BAR, (b + 1) * BAR
    snd = [n for n in pn if n[0] < s1 and n[1] > s0]
    if not snd: continue
    low = min(snd, key=lambda n: n[2])[2]
    pcs = []
    for n in sorted(snd, key=lambda n: -(min(n[1], s1) - max(n[0], s0))):
        if n[2] % 12 not in pcs and n[2] % 12 != low % 12: pcs.append(n[2] % 12)
    bass = 43 + ((low % 12) - 43 % 12) % 12           # G2..F#3
    upper = sorted([60 + pc for pc in pcs[:3]])          # C4..B4
    harp.append([s0, s0 + 2.0, [bass] + upper])
    pedals.append(set([low % 12] + pcs[:3]))

# ---------- percussie: accenten uit het Pro-percussiespoor ----------
perc = []
if PERC != '-' and os.path.exists(PERC):
    import librosa
    y, sr = librosa.load(PERC, sr=22050)
    on = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=False)
    env = librosa.feature.rms(y=y)[0]; thr = env.max() * 0.25
    fr = librosa.time_to_frames(on, sr=sr)
    last = -9
    for t, f in zip(on, fr):
        if env[min(f, len(env) - 1)] >= thr and t - last > 0.6:
            perc.append(qz(t2q(t))); last = t

# ---------- partituur ----------
def tempo_marks():
    t, bpm = ref.get_tempo_changes(); out = []; lastp = None
    for b in range(nbars):
        sec = ref.tick_to_time(int(b * BAR * 2 * TPB))
        i = max(0, np.searchsorted(t, sec, side='right') - 1); q = bpm[i] / 2
        if lastp is None or abs(q - lastp) / lastp > 0.06:
            out.append((b * BAR, int(round(q / 2) * 2))); lastp = q
    return out
TM = tempo_marks()

def make_part(name, inst, clef=None, items=(), kind='note', lyr=None, transpose_check=None):
    p = m.stream.Part(); p.partName = name; inst.partName = name; p.insert(0, inst)
    p.insert(0, m.key.Key('B-')); p.insert(0, m.meter.TimeSignature('4/4'))
    if clef: p.insert(0, clef)
    for it in items:
        s, e = it[0], it[1]
        if kind == 'chord':
            ps = it[2]
            el = m.chord.Chord(ps) if len(ps) > 1 else m.note.Note(ps[0])
        else:
            el = m.note.Note(it[2])
        el.quarterLength = e - s
        if lyr is not None and (lyr, s) in lyr_on: el.lyric = lyr_on[(lyr, s)]
        p.insert(s, el)
    return p

S1 = make_part('Sopraan 1', m.instrument.Soprano(), m.clef.TrebleClef(), voices['S1'], lyr='S1')
S2 = make_part('Sopraan 2', m.instrument.Soprano(), m.clef.TrebleClef(), voices['S2'], lyr='S2')
AL = make_part('Alt', m.instrument.Alto(), m.clef.TrebleClef(), voices['A'], lyr='A')
VN = make_part('Viool', m.instrument.Violin(), m.clef.TrebleClef(), vn)
VC = make_part('Cello', m.instrument.Violoncello(), m.clef.BassClef(), vc)
HP = make_part('Harp', m.instrument.Harp(), m.clef.TrebleClef(), harp, kind='chord')
PRH = make_part('Piano', m.instrument.Piano(), m.clef.TrebleClef(), rh, kind='chord')
PLH = make_part('Piano (lh)', m.instrument.Piano(), m.clef.BassClef(), lh, kind='chord')
PC = m.stream.Part(); PC.partName = 'Percussie'; PC.partAbbreviation = 'Perc.'; pi = m.instrument.SuspendedCymbal() if hasattr(m.instrument, 'SuspendedCymbal') else m.instrument.Percussion()
pi.partName = 'Percussie'; PC.insert(0, pi); PC.insert(0, m.meter.TimeSignature('4/4')); PC.insert(0, m.clef.PercussionClef())
for s in perc:
    n = m.note.Note('B4', quarterLength=1.0); n.expressions.append(m.expressions.TextExpression('cymbal'))
    PC.insert(s, n)
# harp: arpeggio-tekens en pedaalnotatie bij wijziging
NAMES = {10: 'B♭', 11: 'B♮', 3: 'E♭', 4: 'E♮', 8: 'A♭', 9: 'A♮', 1: 'C♯', 0: 'C♮', 6: 'F♯', 5: 'F♮', 2: 'D♮', 7: 'G♮'}
lastped = None
for (s, e, ps), pcset in zip(harp, pedals):
    for el in HP.getElementsByOffset(s):
        if isinstance(el, m.chord.Chord): el.expressions.append(m.expressions.ArpeggioMark())
    alts = ' '.join(NAMES[pc] for pc in sorted(pcset) if pc in (11, 4, 9, 1, 6, 8)) or 'B♭ E♭ (grondstand)'
    if alts != lastped:
        HP.insert(s, m.expressions.TextExpression('pedaal: ' + alts))
        lastped = alts
for off, q in TM:
    S1.insert(off, m.tempo.MetronomeMark(number=q, referent=1.0))

parts = [S1, S2, AL, VN, VC, HP, PRH, PLH, PC]
for p in parts:
    try: p.makeRests(fillGaps=True, inPlace=True, timeRangeFromBarDuration=True)
    except Exception: pass
sc = m.stream.Score()
sc.metadata = m.metadata.Metadata(); sc.metadata.title = "Ce qu'il reste entre nous"; sc.metadata.composer = 'Rebekka Rogiest'
sc.metadata.movementName = 'Werkversie 0.1 (automatisch gegenereerd, niet nagelezen)'
for p in parts: sc.insert(0, p)
sc.insert(0, m.layout.StaffGroup([PRH, PLH], name='Piano', abbreviation='Pno.', symbol='brace'))
sc.write('musicxml', os.path.join(OUT, 'master_v0.1.musicxml'))
sc.write('midi', os.path.join(OUT, 'master_v0.1.mid'))

# ---------- controle ----------
RANGES = {'Sopraan 1': (60, 81), 'Sopraan 2': (58, 77), 'Alt': (53, 74), 'Viool': (55, 100), 'Cello': (36, 81)}
rep = []
for p, src in [(S1, voices['S1']), (S2, voices['S2']), (AL, voices['A']), (VN, vn), (VC, vc)]:
    lo, hi = RANGES[p.partName]
    bad = [(round(n[0] / BAR) + 1, pm.note_number_to_name(n[2])) for n in src if not lo <= n[2] <= hi]
    rep.append(f"{p.partName}: {len(src)} noten, bereik {pm.note_number_to_name(min(n[2] for n in src)) if src else '-'}-{pm.note_number_to_name(max(n[2] for n in src)) if src else '-'}, buiten bereik: {len(bad)} {bad[:8]}")
matched = sum(1 for a, b, s in sm.get_matching_blocks() for _ in range(s))
rep.append(f"Tekst: {len(otoks)} woorden in origineel, {matched} automatisch teruggevonden in de zang, {sum(1 for k in lyr_on if k[0]=='S1' or k[0]=='A')} lettergrepen geplaatst in de melodiestem")
rep.append(f"Maten: {nbars}; tempoaanduidingen: {len(TM)}; percussie-accenten: {len(perc)}; harpakkoorden: {len(harp)}")
rep.append('Melodie per frase: ' + ', '.join(f"m{int(s//BAR)+1}:{v}" for s, e, v in mel_voice_at))
open(os.path.join(OUT, 'controlerapport.txt'), 'w').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

# ---------- partijen apart ----------
groups = {'1_Sopraan_1': [S1], '2_Sopraan_2': [S2], '3_Alt': [AL], '4_Viool': [VN], '5_Cello': [VC], '6_Harp': [HP], '7_Piano': [PRH, PLH], '8_Percussie': [PC]}
for nm, ps in groups.items():
    x = m.stream.Score(); x.metadata = m.metadata.Metadata(); x.metadata.title = "Ce qu'il reste entre nous"
    x.metadata.composer = 'Rebekka Rogiest'; x.metadata.movementName = nm.split('_', 1)[1].replace('_', ' ') + ' (werkversie 0.1)'
    for p in ps: x.insert(0, p)
    if len(ps) == 2: x.insert(0, m.layout.StaffGroup(ps, name='Piano', symbol='brace'))
    x.write('musicxml', os.path.join(OUT, 'partijen', nm + '.musicxml'))
