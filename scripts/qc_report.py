"""Controle per maat: welke maten moet een mens nakijken?
Gebruik: GRIDDIR=... python3 -I qc_report.py <master.musicxml> <map-suno-stems(wav+mid)> <playback.mp3> <controlerapport.txt> <aligned.json> <uitmap>
Combineert: (1) noten partituur vs Suno-MIDI per maat, (2) klankvergelijking origineel vs partituur per maat,
(3) regels: bereik, tekst zonder noot, afwijkende maatsoort. Schrijft controle_per_maat.html + fragmenten.
"""
import sys, os, glob, json, re, subprocess, html
import numpy as np, librosa, soundfile as sf
import mido.midifiles.meta as mm
_o = mm.MetaSpec_key_signature.decode
def _s(self, msg, data):
    try: _o(self, msg, data)
    except Exception: msg.key = 'C'
mm.MetaSpec_key_signature.decode = _s
import pretty_midi as pm, music21 as m
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grid import DPGrid
XML, SRC, PLAY, CTRL, ALIGNED, OUT = sys.argv[1:7]
GD = os.environ['GRIDDIR']
G = DPGrid(np.load(os.path.join(GD, 'beats.npy')), list(np.load(os.path.join(GD, 'bar_starts.npy'))))
NB = len(G.bars); os.makedirs(os.path.join(OUT, 'fragmenten'), exist_ok=True)

# --- 1. noten ---
sc = m.converter.parse(XML)
score_notes = {'zang': [], 'piano': []}
for p in sc.parts:
    grp = 'zang' if p.partName in ('Sopraan 1', 'Sopraan 2', 'Alt') else ('piano' if (p.partName or '').startswith('Piano') else None)
    if not grp: continue
    fl = p.flatten()
    for n in fl.notes:
        for pt in n.pitches: score_notes[grp].append((float(n.getOffsetBySite(fl)), pt.midi))
ref_notes = {'zang': [], 'piano': []}
for f in glob.glob(os.path.join(SRC, '*.mid')):
    grp = 'piano' if '(Piano)' in f else ('zang' if any(k in f for k in ('Vocal', 'Choir')) else None)
    if not grp: continue
    for ins in pm.PrettyMIDI(f).instruments:
        for n in ins.notes:
            if n.velocity >= 20: ref_notes[grp].append((G.q(n.start), n.pitch))
def f1_bar(grp, k, tol=0.3):
    s0, s1 = G.bars[k]
    R = [(q, p % 12) for q, p in ref_notes[grp] if s0 <= q < s1]
    S = [(q, p % 12) for q, p in score_notes[grp] if s0 <= q < s1]
    if not R and not S: return None
    if not R or not S: return 0.0
    used = set(); hit = 0
    for q, pc in S:
        for i, (rq, rpc) in enumerate(R):
            if i not in used and rpc == pc and abs(rq - q) <= tol: used.add(i); hit += 1; break
    pr, rc = hit / len(S), hit / len(R)
    return 0.0 if pr + rc == 0 else 2 * pr * rc / (pr + rc)

# --- 2. klank ---
SR = 22050; HOP = 512
orig = sum(librosa.load(f, sr=SR, mono=True)[0] for f in glob.glob(os.path.join(SRC, '*.wav')))
play, _ = librosa.load(PLAY, sr=SR, mono=True)
n = max(len(orig), len(play)); orig = np.pad(orig, (0, n - len(orig))); play = np.pad(play, (0, n - len(play)))
ca = librosa.feature.chroma_cens(y=orig, sr=SR, hop_length=HOP); cb = librosa.feature.chroma_cens(y=play, sr=SR, hop_length=HOP)
def chroma_dist(k):
    a, b = librosa.time_to_frames([G.sec(G.bars[k][0]), G.sec(G.bars[k][1])], sr=SR, hop_length=HOP)
    A, B = ca[:, a:b].mean(1), cb[:, a:b].mean(1)
    if np.linalg.norm(A) < 1e-6 or np.linalg.norm(B) < 1e-6: return None
    return 1 - float(np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B)))

# --- 3. regels ---
flags = {k: [] for k in range(NB)}
for line in open(CTRL, encoding='utf-8'):
    mm_ = re.match(r"(Sopraan 1|Sopraan 2|Alt|Viool|Cello):.*buiten bereik: \d+ (\[.*\])", line)
    if mm_:
        for b, nm in re.findall(r"\((\d+), '([^']+)'\)", mm_.group(2)):
            if 1 <= int(b) <= NB: flags[int(b) - 1].append(f"{mm_.group(1)}: {nm} buiten comfortabel bereik")
for k in range(NB):
    if G.ts(k) != '4/4': flags[k].append(f"afwijkende maatsoort {G.ts(k)}: nakijken of de maatstreep klopt")

rows = []
cd = [chroma_dist(k) for k in range(NB)]; valid = [x for x in cd if x is not None]
mu, sd = (np.mean(valid), np.std(valid) + 1e-9) if valid else (0, 1)
for k in range(NB):
    fz, fp = f1_bar('zang', k), f1_bar('piano', k)
    c = cd[k]; cz = (c - mu) / sd if c is not None else 0
    reasons = []
    if fz is not None and fz < 0.5: reasons.append(f"zang wijkt af van Suno ({int(fz*100)}% overeenkomst)")
    if fp is not None and fp < 0.5: reasons.append(f"piano wijkt af van Suno ({int(fp*100)}% overeenkomst)")
    if cz > 1.0: reasons.append("klinkt anders dan het origineel (klankvergelijking)")
    reasons += flags[k]
    score = (1 - (fz if fz is not None else 1)) * 0.4 + (1 - (fp if fp is not None else 1)) * 0.25 + max(0, cz) * 0.2 + 0.3 * len(flags[k])
    rows.append(dict(bar=k + 1, t=G.sec(G.bars[k][0]), score=score, reasons=reasons, fz=fz, fp=fp))
rank = sorted([r for r in rows if r['reasons']], key=lambda r: -r['score'])
top = rank[:15]

# fragmenten: origineel en dan partituur, per maat (met halve maat marge)
for r in top:
    k = r['bar'] - 1; a = max(0, G.sec(G.bars[k][0]) - 0.8); b = G.sec(G.bars[k][1]) + 0.8
    seg_o = orig[int(a * SR):int(b * SR)]; seg_p = play[int(a * SR):int(b * SR)]
    norm = lambda x: x / (np.abs(x).max() + 1e-9) * 0.8
    clip = np.concatenate([norm(seg_o), np.zeros(int(0.7 * SR)), norm(seg_p)])
    w = os.path.join(OUT, 'fragmenten', f"maat_{r['bar']:02d}.wav"); sf.write(w, clip, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', w, '-b:a', '128k', w[:-4] + '.mp3']); os.remove(w)

mmss = lambda t: f"{int(t//60)}:{int(t%60):02d}"
avg = lambda xs: int(100 * np.mean([x for x in xs if x is not None]))
summary = dict(maten=NB, zang=avg([r['fz'] for r in rows]), piano=avg([r['fp'] for r in rows]), nakijken=len(rank))
trs = '\n'.join(f"<tr><td class='b'>{r['bar']}</td><td>{mmss(r['t'])}</td><td>{'<br>'.join(html.escape(x) for x in r['reasons'])}</td>"
                f"<td><audio controls preload='none' src='fragmenten/maat_{r['bar']:02d}.mp3'></audio></td></tr>" for r in top)
rest = ', '.join(str(r['bar']) for r in rank[15:])
doc = f"""<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Controle per maat</title><style>
body{{font-family:Inter,system-ui,sans-serif;margin:0;padding:16px;color:#1d1b26;background:#fff;max-width:900px}}
h1{{color:#5b2a6e;font-size:22px;margin:0 0 4px}} p{{line-height:1.5}} .k{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}
.k div{{background:#f6f4f9;border-radius:8px;padding:8px 12px}} .k b{{display:block;font-size:20px;color:#5b2a6e}}
table{{border-collapse:collapse;width:100%;font-size:14px}} td,th{{border-bottom:1px solid #e3e0ea;padding:6px;text-align:left;vertical-align:top}}
td.b{{font-weight:700;font-size:16px}} audio{{width:220px;height:32px}}
</style></head><body>
<h1>Ce qu'il reste entre nous: maten om na te kijken (werkversie 0.3)</h1>
<p>Automatische controle. De computer vergelijkt per maat de partituur met de noten van Suno en met de klank van het origineel. Hij kan niet echt luisteren: dit is een lijst van <b>vermoedelijke</b> problemen, met de ergste bovenaan. Elk fragment speelt eerst het origineel en na een korte stilte de partituur.</p>
<div class="k"><div><b>{summary['maten']}</b>maten</div><div><b>{summary['zang']}%</b>zangnoten gelijk aan Suno</div><div><b>{summary['piano']}%</b>pianonoten gelijk aan Suno</div><div><b>{summary['nakijken']}</b>maten gemarkeerd</div></div>
<table><tr><th>Maat</th><th>Tijd</th><th>Waarom</th><th>Origineel, dan partituur</th></tr>{trs}</table>
<p>Ook gemarkeerd, minder dringend: maat {rest or '-'}.</p>
<p style="color:#5d5a6b;font-size:13px">"Gelijk aan Suno" meet of noten op ongeveer dezelfde plaats en toonhoogte (los van octaaf) staan als in Suno's eigen MIDI. Suno's MIDI is zelf ook een schatting, dus 100% is geen garantie.</p>
</body></html>"""
open(os.path.join(OUT, 'controle_per_maat.html'), 'w', encoding='utf-8').write(doc)
json.dump(dict(summary=summary, ranked=[(r['bar'], r['reasons']) for r in rank]), open(os.path.join(OUT, 'controle_per_maat.json'), 'w'), ensure_ascii=False, indent=1)
print(summary); print([(r['bar'], r['reasons'][:1]) for r in top[:8]])
