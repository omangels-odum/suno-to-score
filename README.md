# suno-to-score

Van een stuk gemaakt in Suno naar een uitvoerbare partituur voor een live ensemble.
Eerste project: *Ce qu'il reste entre nous* (Rebekka Rogiest), voor 6 zangeressen (S1, S2, A, elk dubbel)
met piano, harp, viool, cello en percussie.

## Werkwijze (kort)
1. **Suno Studio (Premier):** Get Stems > Advanced split (Lead Vocal, Backing Vocals, Choir, Piano, Strings);
   download **WAV + MIDI**, *Follow tempo changes*.
2. **Maatraster uit audio:** Beat This! op de volledige mix, tellen verdichten, maatstrepen kiezen op
   harmoniewissels (`scripts/grid.py`).
3. **Tekst:** woordtijden (faster-whisper) en daarna forced alignment van de exacte tekst
   (`scripts/align_lyrics.py`, Frans wav2vec2, Apache-2.0).
4. **Partituur bouwen:** `scripts/build_master_v2.py` (MusicXML + MIDI + partijen + controlerapport).
5. **Gravure:** `scripts/engrave_verovio.py` (Verovio; `engrave.sh` met LilyPond als alternatief).
6. **Audio:** `scripts/render_audio_v2.py` (playback, vergelijking links origineel / rechts partituur, repetitietracks).
7. **Controle per maat:** `scripts/qc_report.py` -> HTML met de maten om na te kijken.
8. **Mens:** Rebekka beluistert, een musicus (Dirk, werkt in Finale) leest na en werkt af via MusicXML.

Zie `docs/AI_BRIEFING.md` (instructies voor een AI), `docs/WERKNOTITIES.md` (alle beslissingen) en
`docs/handleiding.pdf` (handleiding voor Rebekka). Scripts: `scripts/README.md`.

## Mappen
- `scripts/`: alle code (Python 3.13, CPU)
- `docs/`: handleiding, AI-briefing, werknotities
- `projects/<stuk>/`: tekst, uitlijning, maatraster, versies (MusicXML, PDF, controlerapporten)

Audio (stems, mp3) staat bewust niet in git: groot en beschermd. Bewaar die bij het stuk in Suno of lokaal.

## Status
| Versie | Wat | Resultaat |
|---|---|---|
| v0.1 | Suno-MIDI op Suno-tempokaart, vaste 4/4 | volgens Rebekka 30-40% juist; harmoniewissel op tel 1: 8% |
| v0.2 | maatraster uit audio, forced alignment tekst, controle per maat | harmoniewissel op tel 1: 51%; zang 78% / piano 74% gelijk aan Suno-MIDI; Rebekka: "nog niet beter" |
| v0.3 | piano met aangehouden noten en stemmen, geen weggevallen woorden, MusicXML 3.1 voor Finale, Verovio-gravure | pianoklank 81% -> 88% gelijk aan Suno; project daarna gepauzeerd |
