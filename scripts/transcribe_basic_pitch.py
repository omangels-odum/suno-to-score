"""Reserve-transcriptie met Spotify Basic Pitch (open source).
Gebruik: python3 -I transcribe_basic_pitch.py <map-met-wav-stems> <uitvoermap>
Installatie (Python 3.13): pip install basic-pitch --no-deps && pip install onnxruntime resampy pretty_midi mir_eval
Resultaat: één .mid per stem. Toonhoogtes zijn bruikbaar, het ritme niet (geen maatindeling).
Voor de partituur is Klangio de betere bron; dit dient als controle of reserve."""
import sys, glob, os
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, '*.wav'))):
    _, midi, notes = predict(f, model_or_model_path=ICASSP_2022_MODEL_PATH)
    out = os.path.join(dst, os.path.basename(f)[:-4].replace(' ', '_') + '.mid')
    midi.write(out)
    print(out, len(notes), 'noten')
