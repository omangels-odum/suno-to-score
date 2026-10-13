# Scripts

Alle scripts zijn getest met Python 3.13 op Linux. Ze lezen audio- en MIDI-bestanden als data.

| Script | Doet | Installatie |
|---|---|---|
| `analyze.py <map-met-stems>` | Energie per spoor, tempoverloop per 10 s, toonsoort per 20 s (Krumhansl-profielen op chroma) | `pip install librosa` |
| `transcribe_basic_pitch.py <stems> <uit>` | Ruwe MIDI per spoor (reserve voor Klangio) | zie kop van het script |
| `engrave_test.py` | Proef: MIDI > music21 > MusicXML > LilyPond-PNG. Toont waarom quantisatie zonder tempokaart faalt. | `pip install music21 lilypond pretty_midi` |

Gravure: `pip install lilypond` levert de LilyPond-binaries; `musicxml2ly` zit in dezelfde map (`python3 -c "import lilypond;print(lilypond.executable())"`).

Nog te bouwen (stap 4 van de werkwijze): tempokaart voor het hele stuk, samenvoegen van de Klangio-sporen op één maatraster, controle-script (bereik, maatlengtes, parallellen), export van partituur, partijen en repetitie-MP3's.

## Toegevoegd na de Advanced split (13/10/2026)
| Script | Doet |
|---|---|
| `build_master.py <map-met-suno-mid> <words.json> <tekst.txt> <percussie.wav or -> <uit>` | Bouwt de master (MusicXML + MIDI) en partijen uit de Suno-MIDI op de gedeelde tempokaart, met tekst en controlerapport |
| `engrave.sh <bestand.musicxml> <notengrootte>` | MusicXML > LilyPond > PDF |
| `render_audio.py <master.musicxml> <een-suno.mid> <map-met-wav> <uit>` | Playback, vergelijking (links origineel, rechts partituur) en repetitietracks per stem, synchroon met het origineel |
| `midiinfo.py <map>` | Toont noten, bereik en tempokaart van Suno-MIDI |
Woordtijden (words.json): faster-whisper, zie 01_AI_BRIEFING.md §5a.

## Versie 0.2 (13/10/2026)
| Script | Doet |
|---|---|
| (Beat This!) | `pip install beat-this` (+ CPU-torch). Tellen en downbeats uit de volledige mix: zie `grid.py` |
| `grid.py` | Maatraster: tellen verdichten waar de tracker een tel oversloeg; maatstrepen kiezen via dynamisch programmeren op harmoniewissels (laagste pianonoot) + downbeats; 2/4-, 3/4-maten mogen |
| `align_lyrics.py <lead.wav> <tekst.txt> <whisper_words.json> <uit.json>` | Forced alignment van de exacte tekst per regel (wav2vec2 Frans, jonatasgrosman/wav2vec2-large-xlsr-53-french, Apache-2.0) |
| `build_master_v2.py` | Zoals v1 maar op het audio-maatraster (env GRIDDIR met beats.npy + bar_starts.npy), lettergrepen op klinkertijden, ontbrekende zangnoten uit pyin-toonhoogte |
| `render_audio_v2.py` | Playback op het audio-maatraster |
| `qc_report.py` | Controle per maat (noten vs Suno-MIDI, chroma-afstand, regels) -> HTML met fragmenten |
Resultaat v0.2: harmoniewissel op tel 1 in 51% (v0.1: 8%); zang 78% en piano 74% gelijk aan Suno-MIDI; 18 maten gemarkeerd.
