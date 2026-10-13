import librosa, numpy as np, glob, os, sys
d=sys.argv[1]; sr=22050
files=sorted(glob.glob(os.path.join(d,'*.wav')))
ys={}
for f in files:
    y,_=librosa.load(f,sr=sr,mono=True); ys[os.path.basename(f)[:-4]]=y
mix=sum(ys.values())
tot=np.sum(mix**2)
print("dur",len(mix)/sr)
for k,y in ys.items():
    rms=librosa.feature.rms(y=y,frame_length=2048,hop_length=512)[0]
    db=20*np.log10(rms+1e-9); peak=db.max()
    active=np.mean(db>peak-30)
    cent=np.median(librosa.feature.spectral_centroid(y=y,sr=sr)[0][db>peak-30]) if active>0 else 0
    print(f"{k:18s} energy%={100*np.sum(y**2)/tot:6.2f} peakdB={peak:6.1f} active%={100*active:5.1f} centroidHz={cent:7.0f}")
# tempo / beats on mix
onset=librosa.onset.onset_strength(y=mix,sr=sr)
tg=librosa.feature.tempo(onset_envelope=onset,sr=sr,aggregate=None)
t=librosa.times_like(tg,sr=sr)
for s in range(0,int(t[-1]),10):
    i=np.argmin(abs(t-s)); print(f"t={s:4d}s tempo~{tg[i]:.0f}")
# key estimate per 30s via chroma
ch=librosa.feature.chroma_cqt(y=mix,sr=sr)
names='C C# D D# E F F# G G# A A# B'.split()
maj=np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]);mn=np.array([6.33,2.68,3.52,5.38,2.6,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
fr=librosa.frames_to_time(np.arange(ch.shape[1]),sr=sr)
for s in range(0,int(fr[-1]),20):
    seg=ch[:,(fr>=s)&(fr<s+20)].mean(1)
    best=max(((np.corrcoef(np.roll(p,i),seg)[0,1],names[i]+q) for i in range(12) for p,q in ((maj,''),(mn,'m'))))
    print(f"{s:4d}-{s+20}s key~{best[1]} ({best[0]:.2f})")
