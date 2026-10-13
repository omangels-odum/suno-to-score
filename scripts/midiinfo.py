import mido.midifiles.meta as mm, sys, glob, os, numpy as np
_orig=mm.MetaSpec_key_signature.decode
def safe(self,msg,data):
    try: _orig(self,msg,data)
    except Exception: msg.key='C'
mm.MetaSpec_key_signature.decode=safe
import pretty_midi as pm, mido
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*.mid'))):
    raw=mido.MidiFile(f)
    metas=[m for tr in raw.tracks for m in tr if m.is_meta and m.type in('set_tempo','time_signature','key_signature')]
    m=pm.PrettyMIDI(f); t,bpm=m.get_tempo_changes()
    ns=[n for i in m.instruments for n in i.notes]; ps=[n.pitch for n in ns]
    print(os.path.basename(f), '| notes',len(ns),'| range',pm.note_number_to_name(min(ps)),'-',pm.note_number_to_name(max(ps)),
      '| tempo events',len(bpm),'bpm',round(min(bpm),1),'-',round(max(bpm),1),'| timesig',[(x.numerator,x.denominator) for x in m.time_signature_changes][:4],
      '| tracks',[(i.name,i.program,len(i.notes)) for i in m.instruments], '| ticks/beat',raw.ticks_per_beat)
    print('   simultaneous notes avg',round(np.mean([sum(1 for o in ns if o.start<=n.start<o.end) for n in ns]),2),
          '| first note s',round(min(n.start for n in ns),2),'| last end s',round(max(n.end for n in ns),2))
