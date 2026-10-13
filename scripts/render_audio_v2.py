"""Rendert playback van de master op Suno's eigen tempokaart (synchroon met het origineel), plus vergelijking en repetitietracks."""
import sys, os, glob, numpy as np, subprocess
import mido.midifiles.meta as mm
_o=mm.MetaSpec_key_signature.decode
def _s(self,msg,data):
    try:_o(self,msg,data)
    except Exception: msg.key='C'
mm.MetaSpec_key_signature.decode=_s
import pretty_midi as pm, music21 as m, librosa, soundfile as sf
XML, SUNOMID, ORIGDIR, OUT = sys.argv[1:5]
SF='/usr/share/sounds/sf2/default-GM.sf2'; SR=44100
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from grid import DPGrid
GD=os.environ.get('GRIDDIR',os.path.dirname(os.path.abspath(__file__)))
_st=list(np.load(os.path.join(GD,'bar_starts.npy')))
G=DPGrid(np.load(os.path.join(GD,'beats.npy')),_st)
q2s=G.sec
sc=m.converter.parse(XML)
PROG={'Sopraan 1':52,'Sopraan 2':52,'Alt':52,'Viool':40,'Cello':42,'Harp':46,'Piano':0,'Piano (lh)':0,'Percussie':None}
tracks={}
for p in sc.parts:
    name=p.partName or 'Piano'
    prog=PROG.get(name,0)
    ins=pm.Instrument(program=prog or 0,is_drum=prog is None,name=name)
    for n in p.flatten().notes:
        s=n.getOffsetInHierarchy(sc) if False else n.getOffsetBySite(p.flatten())
        e=s+n.quarterLength
        ps=[x.midi for x in n.pitches] if not (prog is None) else [49]
        for k in ps: ins.notes.append(pm.Note(velocity=70 if prog==52 else 60,pitch=k,start=q2s(s),end=max(q2s(e),q2s(s)+0.05)))
    tracks[name]=ins
def synth(insts):
    x=pm.PrettyMIDI(); x.instruments=insts
    return x.fluidsynth(fs=SR,sf2_path=SF)
audio={k:synth([v]) for k,v in tracks.items()}
L=max(len(a) for a in audio.values())
pad=lambda a: np.pad(a,(0,L-len(a)))
def norm(a): return a/ (np.abs(a).max()+1e-9)*0.9
def mp3(a,name,stereo=None):
    w=os.path.join(OUT,name+'.wav'); sf.write(w, stereo if stereo is not None else a, SR)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',w,'-b:a','160k',os.path.join(OUT,name+'.mp3')]); os.remove(w)
os.makedirs(OUT,exist_ok=True)
full=norm(sum(pad(a) for a in audio.values())); mp3(full,'playback_partituur')
# vergelijking: links origineel, rechts partituur
orig=sum(librosa.load(f,sr=SR,mono=True)[0] for f in glob.glob(os.path.join(ORIGDIR,'*.wav')))
n=max(len(orig),L); o=norm(np.pad(orig,(0,n-len(orig)))); f=np.pad(full,(0,n-len(full)))
mp3(None,'vergelijking_links-origineel_rechts-partituur',np.stack([o,f],1))
# repetitietracks
for v in ['Sopraan 1','Sopraan 2','Alt']:
    mix=sum(pad(a)*(1.0 if k==v else 0.22) for k,a in audio.items()); mp3(norm(mix),'repetitie_'+v.replace(' ','_'))
print('ok', round(L/SR,1),'s')
