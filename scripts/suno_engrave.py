import mido.midifiles.meta as mm, sys
_o=mm.MetaSpec_key_signature.decode
def safe(self,msg,data):
    try:_o(self,msg,data)
    except Exception: msg.key='C'
mm.MetaSpec_key_signature.decode=safe
import mido, music21 as m
src,out,bars=sys.argv[1],sys.argv[2],int(sys.argv[3])
mf=mido.MidiFile(src); tpb=mf.ticks_per_beat
notes=[]
for tr in mf.tracks:
    t=0; on={}
    for msg in tr:
        t+=msg.time
        if msg.type=='note_on' and msg.velocity>0: on[msg.note]=t
        elif msg.type in('note_off','note_on') and msg.note in on:
            s=on.pop(msg.note); notes.append((s/tpb,(t-s)/tpb,msg.note))
q=lambda x: round(x*2)/2
p=m.stream.Part(); p.insert(0,m.instrument.Soprano()); p.insert(0,m.key.Key('B-')); p.insert(0,m.meter.TimeSignature('4/4'))
notes.sort(key=lambda n:(q(n[0]),-n[2])); last=-1
for s,d,pitch in notes:
    o=q(s)
    if o>=bars*4: break
    if o<=last: continue
    p.insert(o,m.note.Note(pitch,quarterLength=max(0.5,q(d)))); last=o
p=p.makeRests(fillGaps=True,inPlace=False).makeNotation()
sc=m.stream.Score([p]); sc.metadata=m.metadata.Metadata(title='Suno MIDI test (Lead Vocal)'); sc.write('musicxml',out)
