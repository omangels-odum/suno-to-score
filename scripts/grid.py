"""Maatraster uit audio: Beat This!-tellen en -downbeats -> maten (in achtsten = 1 Beat This-tel).
Gebruik als module: g = Grid(beats.npy, down.npy); g.q(sec) -> kwartnoot-positie; g.bars -> [(start_q, end_q)]
"""
import numpy as np

class Grid:
    def __init__(self, beats, down, target=8, allowed=(6, 8, 10)):
        self.beats = np.asarray(beats, float)
        b = self.beats
        ib = np.diff(b); self.ibi = float(np.median(ib))
        # downbeats -> tel-index
        didx = sorted(set(int(np.argmin(abs(b - d))) for d in down))
        dset = set(didx)
        starts = [0]
        i = 0
        while i < len(b) - 1:
            cands = [j for j in dset if (j - i) in allowed]
            if cands:
                j = min(cands, key=lambda j: (abs(j - i - target), j))
            else:
                j = i + target
            if j >= len(b): break
            starts.append(j); i = j
        self.bar_beats = starts                       # tel-index van elke maatstart
        self.bars = []
        for a, c in zip(starts, starts[1:] + [len(b) - 1 + (target - (len(b) - 1 - starts[-1]) if len(b) - 1 - starts[-1] < target else 0)]):
            self.bars.append((a / 2.0, c / 2.0))
    def frac(self, sec):
        b = self.beats
        if sec <= b[0]: return (sec - b[0]) / self.ibi
        if sec >= b[-1]: return (len(b) - 1) + (sec - b[-1]) / self.ibi
        i = np.searchsorted(b, sec) - 1
        return i + (sec - b[i]) / (b[i + 1] - b[i])
    def q(self, sec):
        return self.frac(sec) / 2.0
    def sec(self, q):
        x = q * 2.0; b = self.beats
        if x <= 0: return b[0] + x * self.ibi
        if x >= len(b) - 1: return b[-1] + (x - len(b) + 1) * self.ibi
        i = int(x); return b[i] + (x - i) * (b[i + 1] - b[i])
    def barno(self, q):
        for k, (s, e) in enumerate(self.bars):
            if s <= q < e: return k + 1
        return len(self.bars)
    def ts(self, k):
        s, e = self.bars[k]; n8 = int(round((e - s) * 2))
        return {6: '3/4', 8: '4/4', 10: '5/4', 4: '2/4', 12: '6/4'}.get(n8, f'{n8}/8')
    def qbpm(self, k):
        s, e = self.bars[k]
        i0, i1 = int(s * 2), min(int(e * 2), len(self.beats) - 1)
        if i1 <= i0: return 60 / (2 * self.ibi)
        return 60 / (2 * float(np.median(np.diff(self.beats[i0:i1 + 1]))))

def dp_bars(nbeats, hits, allowed=(8, 6, 4, 10), pen={8: 0.0, 6: 1.5, 4: 1.5, 10: 2.0}, pickup_max=8):
    """Kies maatstarts (tel-indices) die zoveel mogelijk 'hits' (harmoniewissels, downbeats) op tel 1 leggen.
    Strafpunten voor maten die geen 4/4 zijn. Eerste maat mag een opmaat zijn (1..pickup_max tellen)."""
    NEG = -1e9
    best = np.full(nbeats + 1, NEG); prev = np.full(nbeats + 1, -1, int)
    best[0] = hits[0]
    for p in range(1, pickup_max + 1):      # opmaat
        if p <= nbeats and hits[p] + 0.0 > best[p]: best[p] = hits[p] - 0.5; prev[p] = 0
    for j in range(1, nbeats + 1):
        for L in allowed:
            i = j - L
            if i >= 0 and best[i] > NEG / 2:
                v = best[i] + (hits[j] if j < len(hits) else 0) - pen[L]
                if v > best[j]: best[j] = v; prev[j] = i
    # einde: beste eindpunt in de laatste 10 tellen
    end = max(range(max(0, nbeats - 10), nbeats + 1), key=lambda j: best[j])
    path = [end]
    while prev[path[-1]] >= 0: path.append(prev[path[-1]])
    path = path[::-1]
    if path[0] != 0: path = [0] + path
    return path

def densify(beats):
    """Waar de tracker een tel oversloeg (interval > 1,6x mediaan), tussenliggende tellen invoegen."""
    b = list(np.asarray(beats, float)); med = float(np.median(np.diff(b))); out = [b[0]]
    for x in b[1:]:
        gap = x - out[-1]; n = int(round(gap / med))
        if n >= 2 and gap > 1.6 * med:
            for k in range(1, n): out.append(out[-1] + gap / n) if False else None
            step = gap / n; base = out[-1]
            out.extend(base + step * k for k in range(1, n))
        out.append(x)
    return np.array(out)

class DPGrid(Grid):
    def __init__(self, beats, starts):
        self.beats = np.asarray(beats, float); self.ibi = float(np.median(np.diff(self.beats)))
        self.bar_beats = list(starts)
        ends = self.bar_beats[1:] + [self.bar_beats[-1] + 8]
        self.bars = [(a / 2.0, c / 2.0) for a, c in zip(self.bar_beats, ends)]
