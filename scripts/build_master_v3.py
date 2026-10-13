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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grid import DPGrid
GRIDDIR = os.environ.get('GRIDDIR', os.path.dirname(os.path.abspath(__file__)))
_beats = np.load(os.path.join(GRIDDIR, 'beats.npy')); _st = list(np.load(os.path.join(GRIDDIR, 'bar_starts.npy')))
# twee opeenvolgende 2/4-maten samenvoegen tot één 4/4-maat
k = 0
while k < len(_st) - 2:
    if _st[k + 1] - _st[k] == 4 and _st[k + 2] - _st[k + 1] == 4: del _st[k + 1]
    k += 1
G = DPGrid(_beats, _st)
def t2q(sec):       # seconden -> kwartnoot-positie op het audio-maatraster
    return G.q(sec)
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
    """Eén noot tegelijk. Echt gelijktijdige noten (<60 ms): hoogste/laagste houden.
    Snel opeenvolgende noten die op dezelfde zestiende vallen: de latere schuift een zestiende op."""
    ns = sorted(ns, key=lambda n: (n[0], n[3] if n[3] is not None else 0))
    seq = []
    for n in ns:
        n = list(n)
        if seq:
            p = seq[-1]
            same = (n[3] is not None and p[3] is not None and abs(n[3] - p[3]) < 0.06) or (n[3] is None and n[0] == p[0])
            if same:
                if (n[2] > p[2]) == (prefer == 'high'): seq[-1] = n
                continue
            if n[0] <= p[0]:
                n[0] = p[0] + Q
                if n[1] < n[0] + Q: n[1] = n[0] + Q
        seq.append(n)
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

# ---------- tekst (forced alignment, zie align_lyrics.py) ----------
VOW = 'aeiouyàâäéèêëîïôöûùüœæ'
def syllables(w):
    """Franse lettergrepen voor zang: medeklinker tussen klinkers gaat naar de volgende lettergreep;
    een stomme e op het einde blijft een aparte lettergreep (wordt later geschrapt als er geen noot voor is)."""
    core = w.strip(".,;:!?…")
    parts = [p for p in re.split(rf"([{VOW}]+)", core, flags=re.I) if p != '']
    res, buf = [], ''
    for t in parts:
        if re.fullmatch(rf"[{VOW}]+", t, flags=re.I): res.append(buf + t); buf = ''
        else:
            if res and len(t) > 1:
                keep = 2 if (len(t) >= 2 and t[-2:].lower() in ('ch', 'qu', 'gn', 'ph', 'th') or (len(t) >= 2 and t[-1].lower() in 'lr' and t[-2].lower() in 'bcdfgptv')) else 1
                res[-1] += t[:-keep]; buf = t[-keep:]
            else: buf += t
    if buf:
        if res: res[-1] += buf
        else: res = [buf]
    # "qu"/"gu" + klinker horen samen
    return res or [core]
def is_mute(syl, last):
    return last and re.fullmatch(r"[^aeiouyàâéèêëîïôûùü]*e(s|nt)?[^a-z]*", syl.lower()) is not None
ALW = json.load(open(WORDS))      # [{word,start,end,chars:[(c,s,e)]}]
mel = sorted([(n[3], n[0], v) for v in voices for n in voices[v] if n[3] is not None])   # (sec, q, voice)
import librosa as _lb
_F0P = os.path.join(OUT, 'f0_lead.npy')
if os.path.exists(_F0P): _f0 = np.load(_F0P)
else:
    _y, _ = _lb.load(glob.glob(os.path.join(SRC, '*(Lead Vocal).wav'))[0], sr=16000)
    _f, _v, _ = _lb.pyin(_y, fmin=140, fmax=1000, sr=16000, hop_length=320, frame_length=1280)
    _f0 = np.where(_v, _f, np.nan); np.save(_F0P, _f0)
def f0_pitch(t0, t1):
    a, b = int(t0 / 0.02), max(int(t0 / 0.02) + 2, int(t1 / 0.02))
    seg = _f0[a:b]; seg = seg[~np.isnan(seg)]
    if len(seg) < 3: return None
    return int(round(_lb.hz_to_midi(np.median(seg))))
added = 0; joined = 0
DBG = []; lyr_on = {}; ptr = 0; placed = 0; skipped = 0; flags = []
for wi, wd in enumerate(ALW):
    syl = syllables(wd['word'])
    # tijd per lettergreep = begin van de eerste klinker in die lettergreep
    chars = wd['chars']; ci = 0; stimes = []
    for sy in syl:
        t = None
        for ch in sy.lower():
            while ci < len(chars) and chars[ci][0] != ch: ci += 1
            if ci < len(chars):
                if t is None or ch in VOW: t = chars[ci][1] if t is None or ch not in VOW else chars[ci][1]
                ci += 1
        stimes.append(t if t is not None else wd['start'])
    nxt_word = ALW[wi + 1]["start"] if wi + 1 < len(ALW) else 1e9
    for k, (sy, ts) in enumerate(zip(syl, stimes)):
        tnext = stimes[k + 1] if k + 1 < len(syl) else nxt_word
        best = None
        for j in range(ptr, len(mel)):
            st = mel[j][0]
            if st > max(tnext, ts + 0.25) - 0.05: break
            if st < ts - 0.35: continue
            if best is None or abs(st - ts) < abs(mel[best][0] - ts): best = j
        hy = '-' if k < len(syl) - 1 else ''
        if best is None and not is_mute(sy, k == len(syl) - 1) and (ptr == 0 or ts > mel[ptr - 1][0] + 0.12):
            # geen Suno-noot: toonhoogte uit de audio halen en een noot toevoegen
            pch = f0_pitch(ts, min(tnext, ts + 0.6))
            qq = qz(t2q(ts))
            vv = mel_voice(qq) or 'S1'
            if pch is not None and all(n[0] != qq for n in voices[vv]):
                nq = min([n[0] for n in voices[vv] if n[0] > qq] + [qz(t2q(min(tnext, ts + 0.8)))])
                if nq - qq >= Q:
                    for n in voices[vv]:
                        if n[0] < qq < n[1]: n[1] = qq
                    voices[vv].append([qq, nq, pch, ts]); voices[vv].sort(key=lambda n: n[0])
                    mel.insert(ptr, (ts, qq, vv)); best = ptr; added += 1
        if best is None:
            # geen noot: lettergreep bij de vorige voegen (stomme e of samentrekking)
            skipped += 1; DBG.append((round(ts,2), sy, None))
            prevk = [key for key in lyr_on if key[2] == wi]
            if prevk:
                key = max(prevk, key=lambda x: x[1]); lyr_on[key] = lyr_on[key].rstrip('-') + sy + hy
            elif not is_mute(sy, k == len(syl) - 1):
                # v0.3: woord zonder eigen noot niet laten vallen, maar bij de vorige noot zetten (geen halve zinnen)
                if lyr_on:
                    lastkey = max(lyr_on, key=lambda x: (x[1], x[2]))
                    lyr_on[lastkey] = lyr_on[lastkey].rstrip('-') + ' ' + sy + hy
                    joined += 1
                else: flags.append(wd['word'])
            continue
        key = (mel[best][2], mel[best][1], wi)
        lyr_on[key] = sy + hy; placed += 1; ptr = best + 1
        DBG.append((round(ts,2), sy, round(mel[best][0],2)))
lyr_on = {(v, q): t for (v, q, wi), t in lyr_on.items()}
json.dump(DBG, open(os.path.join(OUT,'lyr_debug.json'),'w'), ensure_ascii=False)
otoks = ALW
class _SM:
    def get_matching_blocks(self): return [(0, 0, len(ALW))]
sm = _SM()
# homoritmische harmoniestemmen krijgen dezelfde tekst
melkeys = {s: t for (v, s), t in lyr_on.items()}
for v in voices:
    for n in voices[v]:
        if (v, n[0]) not in lyr_on and n[0] in melkeys: lyr_on[(v, n[0])] = melkeys[n[0]]

# ---------- piano ----------
pn = [n for n in notes_of('Piano', minvel=20)]
def chords(ns, maxn=8):
    """v0.3: noten houden hun echte duur (aangehouden bas/pedaalklank blijft); geen akkoordsnoei.
    Noten met dezelfde aanslag en ongeveer dezelfde duur worden één akkoord; overlappingen worden later stemmen."""
    by = {}
    for s, e, p, _ in ns:
        e = max(e, s + Q)
        key = (s, round((e - s) / 0.5) * 0.5)          # duur afgerond op achtsten om akkoorden te bundelen
        by.setdefault(key, set()).add(p)
    out = []
    for (s, d), ps in sorted(by.items()):
        ps = sorted(ps)
        if len(ps) > maxn: ps = [ps[0]] + ps[-(maxn - 1):]
        out.append([s, s + max(Q, d), ps])
    return out
def cap_voices(ev, k=3):
    """Maximaal k gelijktijdige stemmen per notenbalk: lukt het niet, dan wordt de vroegst eindigende noot ingekort."""
    ev = sorted(ev, key=lambda x: (x[0], -(x[1] - x[0])))
    ends = []   # [eindtijd, event]
    for e_ in ev:
        ends = [x for x in ends if x[0] > e_[0]]
        if len(ends) >= k:
            x = min(ends, key=lambda x: x[0]); x[1][1] = max(x[1][0] + Q, e_[0]); ends.remove(x)
        ends.append([e_[1], e_])
    return [e_ for e_ in ev if e_[1] - e_[0] >= Q]
rh = cap_voices(chords([n for n in pn if n[2] >= 60])); lh = cap_voices(chords([n for n in pn if n[2] < 60]))

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
nbars = len(G.bars)
harp = []; pedals = []
for b in range(nbars):
    s0, s1 = G.bars[b]
    snd = [n for n in pn if n[0] < s1 and n[1] > s0]
    if not snd: continue
    low = min(snd, key=lambda n: n[2])[2]
    pcs = []
    for n in sorted(snd, key=lambda n: -(min(n[1], s1) - max(n[0], s0))):
        if n[2] % 12 not in pcs and n[2] % 12 != low % 12: pcs.append(n[2] % 12)
    bass = 43 + ((low % 12) - 43 % 12) % 12           # G2..F#3
    upper = sorted([60 + pc for pc in pcs[:3]])          # C4..B4
    harp.append([s0, s0 + min(2.0, s1 - s0), [bass] + upper])
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
    out = []; lastp = None
    for b in range(nbars):
        q = G.qbpm(b)
        if lastp is None or abs(q - lastp) / lastp > 0.08:
            out.append((G.bars[b][0], int(round(q / 2) * 2))); lastp = q
    return out
TM = tempo_marks()

def to31(path):
    """Finale (tot en met v27) importeert MusicXML tot versie 3.1: kop en versienummer aanpassen."""
    t = open(path, encoding='utf-8').read()
    t = t.replace('"-//Recordare//DTD MusicXML 4.0 Partwise//EN"', '"-//Recordare//DTD MusicXML 3.1 Partwise//EN"')
    t = t.replace('http://www.musicxml.org/dtds/partwise.dtd', 'http://www.musicxml.org/dtds/partwise.dtd')
    t = re.sub(r'<score-partwise version="4\.0">', '<score-partwise version="3.1">', t)
    open(path, 'w', encoding='utf-8').write(t)

def add_ts(p):
    last = None
    for k in range(nbars):
        t = G.ts(k)
        if t != last: p.insert(G.bars[k][0], m.meter.TimeSignature(t)); last = t

def make_part(name, inst, clef=None, items=(), kind='note', lyr=None, transpose_check=None, cls=None):
    p = (cls or m.stream.Part)(); p.partName = name; inst.partName = name; p.insert(0, inst)
    p.insert(0, m.key.Key('B-')); add_ts(p)
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
PRH = make_part('Piano', m.instrument.Piano(), m.clef.TrebleClef(), rh, kind='chord', cls=m.stream.PartStaff)
PRH.insert(0, m.expressions.TextExpression('con Ped.'))
PLH = make_part('Piano', m.instrument.Piano(), m.clef.BassClef(), lh, kind='chord', cls=m.stream.PartStaff)
PC = m.stream.Part(); PC.partName = 'Percussie'; PC.partAbbreviation = 'Perc.'; pi = m.instrument.SuspendedCymbal() if hasattr(m.instrument, 'SuspendedCymbal') else m.instrument.Percussion()
pi.partName = 'Percussie'; PC.insert(0, pi); add_ts(PC); PC.insert(0, m.clef.PercussionClef())
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
    if p in (PRH, PLH):
        # overlappende noten (aangehouden bas onder gebroken akkoorden) -> aparte stemmen per maat (Finale: max 4 lagen)
        p.makeMeasures(inPlace=True)
        p.makeTies(inPlace=True)
        # maatsoorten opnieuw correct per maat zetten (makeMeasures schuift ze anders een maat op)
        for k_, me in enumerate(p.getElementsByClass('Measure')):
            for t_ in list(me.recurse().getElementsByClass('TimeSignature')): t_.activeSite.remove(t_)
            if k_ < nbars and (k_ == 0 or G.ts(k_) != G.ts(k_ - 1)): me.timeSignature = m.meter.TimeSignature(G.ts(k_))
        for me in p.getElementsByClass('Measure'):
            if any(a_.offset < b_.offset + b_.quarterLength and b_.offset < a_.offset + a_.quarterLength and a_ is not b_
                   for a_ in me.notes for b_ in me.notes):
                me.makeVoices(inPlace=True, fillGaps=True)
                for i_, v_ in enumerate(me.voices): v_.id = str(i_ + 1)
            else:
                me.makeRests(fillGaps=True, inPlace=True, timeRangeFromBarDuration=True)
        continue
    try: p.makeRests(fillGaps=True, inPlace=True, timeRangeFromBarDuration=True)
    except Exception: pass
sc = m.stream.Score()
sc.metadata = m.metadata.Metadata(); sc.metadata.title = "Ce qu'il reste entre nous"; sc.metadata.composer = 'Rebekka Rogiest'
sc.metadata.movementName = 'Werkversie 0.3 (automatisch gegenereerd, niet nagelezen)'
for p in parts: sc.insert(0, p)
sc.insert(0, m.layout.StaffGroup([PRH, PLH], name='Piano', abbreviation='Pno.', symbol='brace'))
sc.write('musicxml', os.path.join(OUT, 'master_v0.3.musicxml')); to31(os.path.join(OUT, 'master_v0.3.musicxml'))
try: sc.write('midi', os.path.join(OUT, 'master_v0.3.mid'))
except Exception as ex: print('MIDI-export overgeslagen:', ex)

# ---------- controle ----------
RANGES = {'Sopraan 1': (60, 81), 'Sopraan 2': (58, 77), 'Alt': (53, 74), 'Viool': (55, 100), 'Cello': (36, 81)}
rep = []
for p, src in [(S1, voices['S1']), (S2, voices['S2']), (AL, voices['A']), (VN, vn), (VC, vc)]:
    lo, hi = RANGES[p.partName]
    bad = [(G.barno(n[0]), pm.note_number_to_name(n[2])) for n in src if not lo <= n[2] <= hi]
    rep.append(f"{p.partName}: {len(src)} noten, bereik {pm.note_number_to_name(min(n[2] for n in src)) if src else '-'}-{pm.note_number_to_name(max(n[2] for n in src)) if src else '-'}, buiten bereik: {len(bad)} {bad[:8]}")
matched = sum(1 for a, b, s in sm.get_matching_blocks() for _ in range(s))
rep.append(f"Tekst: {len(ALW)} woorden uitgelijnd op de zang; {placed} lettergrepen op een noot, {skipped} samengevoegd met de vorige; {added} noten uit de audio toegevoegd; {joined} woorden zonder eigen noot bij de vorige noot gezet; woorden zonder noot: {flags[:12]}")
rep.append(f"Maatsoorten: {dict((t, sum(1 for k in range(nbars) if G.ts(k)==t)) for t in set(G.ts(k) for k in range(nbars)))}")
rep.append(f"Maten: {nbars}; tempoaanduidingen: {len(TM)}; percussie-accenten: {len(perc)}; harpakkoorden: {len(harp)}")
rep.append('Melodie per frase: ' + ', '.join(f"m{G.barno(s)}:{v}" for s, e, v in mel_voice_at))
open(os.path.join(OUT, 'controlerapport.txt'), 'w').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

# ---------- partijen apart ----------
groups = {'1_Sopraan_1': [S1], '2_Sopraan_2': [S2], '3_Alt': [AL], '4_Viool': [VN], '5_Cello': [VC], '6_Harp': [HP], '7_Piano': [PRH, PLH], '8_Percussie': [PC]}
for nm, ps in groups.items():
    x = m.stream.Score(); x.metadata = m.metadata.Metadata(); x.metadata.title = "Ce qu'il reste entre nous"
    x.metadata.composer = 'Rebekka Rogiest'; x.metadata.movementName = nm.split('_', 1)[1].replace('_', ' ') + ' (werkversie 0.3)'
    for p in ps: x.insert(0, p)
    if len(ps) == 2: x.insert(0, m.layout.StaffGroup(ps, name='Piano', symbol='brace'))
    x.write('musicxml', os.path.join(OUT, 'partijen', nm + '.musicxml')); to31(os.path.join(OUT, 'partijen', nm + '.musicxml'))
