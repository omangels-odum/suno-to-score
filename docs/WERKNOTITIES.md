# Notities: van Suno-stuk naar partituur (voor de handleiding voor Rebekka)

Werknotities, aangevuld tijdens het eerste project ("Ce qu'il reste entre nous", 13/10/2026).
Wordt later uitgewerkt tot een handleiding + zip.

## Einddoel
- Partituur die live uitgevoerd kan worden en klinkt zoals de Suno-mp3.
- Eerste bezetting: 11 op het podium. 6 zangeressen (sopraan 1, sopraan 2, alt, elk dubbel bezet)
  + piano, harp, viool, cello, percussie.
- Output: volledige partituur (dirigent), aparte partijen per muzikant (PDF), MusicXML (bewerkbaar in MuseScore), playback-audio.
- Andere bezettingen (koor van 35, a cappella, groter orkest) vertrekken telkens van dezelfde "master".

## Suno-abonnementen: wat telt voor dit doel
- Pro: stem-scheiding "Auto split" (tot 12 vaste categorieën) en "Split from mix" (één instrument + de rest). Geen Studio.
- Premier: daarbovenop Suno Studio + "Advanced split" (zelf kiezen uit ~100 instrumenten, elk spoor wordt opnieuw opgebouwd i.p.v. uitgefilterd) + MIDI-export van instrumentsporen ("Get MIDI").
- Get MIDI werkt NIET op zang, en geeft ruwe noten zonder maatindeling.
- Geen enkele tool haalt zes afzonderlijke koorstemmen uit een mix: koor komt altijd als één spoor. Die stemmen worden herschreven op basis van de harmonie.
- Advanced split kost 10 credits per stem, Auto split 50 credits per extractie, Get MIDI 10 credits per stem.

## Studio (Premier): hoe Rebekka er betere muziek mee kan maken
- Pro = prompt geven en kiezen uit wat Suno maakt. Studio = zelf meecomponeren.
- Per spoor en per deel werken: alleen het middenstuk opnieuw laten maken.
- Lagen toevoegen aan een bestaand nummer (bv. cello of harp onder een a-cappellastuk).
- Zelf noten ingeven of inspelen (MIDI): haar eigen melodie/akkoorden worden het vertrekpunt.
- Afmixen: volume per spoor, in-/uitvloeien, effecten (basic).

## Exporteren: de juiste instellingen
- Downloaden, niet opnieuw "Extract" klikken (dat kost credits en levert niets extra op).
- Formaat: WAV (niet MP3).
- Tempo: "Follow tempo changes" (niet "Fixed tempo"), zodat tempowisselingen bewaard blijven.
- "Match project tempo" uitzetten in het stems-venster.
- "Unlock & continue" kost één download; daarna zijn alle stems van dat nummer vrij.
- Ook het volledige nummer als WAV downloaden.
- Bestanden per nummer bundelen in één zip.

## Klangio (transcriptie naar noten)
- Doet iets anders dan de Advanced split: split = schonere audio, Klangio = noten met ritme, maatstrepen en maatsoorten (MusicXML), ook voor zang.
- Eerst gratis testen op het zangspoor en vergelijken, pas dan betalen.
- NUANCE: componeert Rebekka nieuwe stukken in Studio door zelf noten in te geven, dan bestaan die noten al exact en is Klangio voor die stukken overbodig. Klangio is vooral nodig voor bestaande stukken die alleen als audio bestaan (zoals "Ce qu'il reste entre nous").
- Tip die daaruit volgt: wie een stuk wil laten uitvoeren, werkt best vanaf het begin met eigen MIDI-noten in Studio. Dat maakt de partituur later veel nauwkeuriger en sneller.

## Klangio: app of API (onderzocht 13/10/2026)
- App "Transcription Studio": zang, piano, strijkers, blazers, synth, bas, gitaar, drums; meerdere instrumenten uit één bestand. Harp niet vermeld.
- Export: PDF, MusicXML, MIDI (gekwantiseerd én ongekwantiseerd), LilyPond.
- Preset "Classic" kiezen voor orkestraal/klassiek materiaal.
- Gratis voorproef zonder account (eerste ~20 s, geen volledige export).
- Prijs volgens een concurrent (Songscription): Transcription Studio Pro ca. $20/maand maandelijks of ca. $8,50/maand jaarlijks. Zelf nakijken bij het afsluiten.
- API: transcriptie enkel voor piano, gitaar, bas en zang (geen strijkers); ook beat-/maatdetectie. Gratis testplan max. 15 s per fragment; Startup $99/maand (500 aanvragen, max. 300 s audio). Aanvragen via formulier.
- Keuze: app, niet API, zolang het om losse stukken gaat. API pas zinvol als dit een herhaald, geautomatiseerd proces wordt.

## Klangio: modus kiezen
- Zangspoor of één instrument: "Single-Instrument" (dan vocals/piano kiezen).
- Meerdere stemmen of strijkers samen in één spoor: "Ensemble & Orchestral".
- Instellingen eerste test (zangspoor): Single-Instrument > Vocals (niet Soprano/Alto: dat zijn saxofoons), lyrics Yes + taal Français, "more options": toonsoort opgeven (hier B♭ major / G minor), maatsoort en tempo Detect, quantization Eighth, triplets No, voice type Soprano.
- "Arrangement" maakt een vereenvoudigde speelversie, geen transcriptie: niet gebruiken voor de partituur.

- Resultaat eerste test (20 s, Pro-stem zang): duidelijk beter dan open source. Leesbaar ritme, tempowissel herkend (61 > 78 BPM), Franse tekst grotendeels juist ("mon voix" moet "ma voix" zijn), akkoordsymbolen. Aandachtspunt: enkele noten zakken ver onder de notenbalk (octaaffout of tweede stem).
- Na de transcriptie: luisteren met "Synth sound" naast "Original sound" om fouten te horen.

## Onderzoek pro-niveau (13/10/2026)
- Geen enkele tool maakt in één keer een uitvoerbare partituur van een rubato-stuk; overal is menselijke afwerking nodig.
- Grootste hefboom: eerst een tempokaart (waar vallen de tellen en maatstrepen), dan pas noten op dat raster zetten. Beat This! (open source) als start, handmatig bijsturen; Melodyne Studio Tempo Editor als professionele tool.
- Elke stem apart transcriberen (monofone sporen) is veel nauwkeuriger dan een mix.
- Claude/ChatGPT kunnen geen audio "beluisteren", wel scripts schrijven die MusicXML bewerken en controleren (bereik per stem, parallellen, maatlengtes). Altijd laten renderen en vergelijken.
- Eindafwerking in notatiesoftware: Dorico (sterkst, betalend) of MuseScore 4 (gratis). MCP "mcp-score" laat Claude MuseScore bedienen (alpha).
- Repetitietracks voor zangers: per stem een MP3 met die stem luider ("part-dominant"), rechtstreeks uit MuseScore/Dorico. ACE Studio 2 (AI-koor) als duurdere optie.
- Kwaliteitscontrole: playback naast het origineel, plus nalezing door een kopiist of musicus die het niet zelf maakte. Richtprijs kopiist (Canada, 2025): CAD 35-48 per partituurpagina, 10-12 per partijpagina; lokaal offertes vragen.
- Rechten: Suno Pro/Premier geven commercieel gebruiksrecht, maar geen garantie op auteursrecht. SABAM: werk registreren in MyWorx en AI-gebruik aangeven ("AI als assistent", "AI als component", "volledig AI"); volledig AI-werk is niet beschermd. Prompts, stems en downloaddata bewaren.

## Wat het eerste stuk leerde (analyse van de Pro-stems)
- Toonsoort Bes groot / g klein, vrij tempo (rubato), geen vaste maat: het ritme is het moeilijkste deel van de omzetting.
- Klankverdeling: zang 68 %, piano 14 %, "synth" (wellicht strijkerspad) 9 %, backing vocals 6,5 %, gitaar en percussie bijna niets, "Other" leeg.
- Auto split kent geen harp, viool of cello: die belanden onder "Guitar", "Synth" of "Other".

## Praktisch
- Factuur/abonnement loopt via Stripe; bij problemen support@suno.com met factuurnummer.
- Deel geen screenshots van de Stripe-pagina: de adresbalk bevat een tijdelijke toegangslink.

## Advanced split + MIDI-download (Premier, 13/10/2026): doorbraak
- Download-venster van de Advanced split heeft naast MP3/WAV ook een vinkje MIDI. Aanvinken: WAV + MIDI, Follow tempo changes.
- Suno levert dan MIDI voor ALLE sporen, ook zang (Lead Vocal, Backing Vocals, Choir), piano en strijkers. (Eerdere bronnen zeiden "geen MIDI voor zang": klopt niet meer.)
- Alle MIDI-bestanden delen dezelfde tempokaart (446 tempowijzigingen, 122-153 BPM): één gemeenschappelijk maatraster voor alle sporen. Dat lost het uitlijnprobleem op.
- Test: Lead Vocal-MIDI op Suno's eigen raster, gekwantiseerd op achtsten, geeft een leesbare melodielijn (beter dan open source, vergelijkbaar met Klangio). Klangio blijft nuttig voor de tekst onder de noten en als tweede mening.
- Technisch: Suno-MIDI bevat een ongeldige toonsoort-meta (12 kruisen); mido/pretty_midi crasht erop. Oplossen door key_signature-decode te omzeilen (zie scripts/midiinfo.py).
- Klankaandeel Advanced split: Lead Vocal 61 %, Piano 16 %, Backing Vocals 5 %, Choir 2 %, Strings 0,3 % (strijkers zijn een zachte laag in het middenstuk). Bereik: Lead F3-F5, Backing/Choir G3-D5, Piano A#1-F7, Strings G1-D5.

## Feedback Rebekka op v0.1 (13/10/2026) en verbeterplan v0.2
- Feedback: "nog veel fouten (maten die er niet in zitten, halve zinnen), maar grote stukken kloppen". Ze kan de partituur meelezen met de audio en fouten aanwijzen.
- Oorzaak maten: vaste 4/4 vanaf tik 0 + aanname "1 Suno-tel = achtste". Oplossing: maatstrepen uit de audio (Beat This!, pip beat-this, MIT), eerste downbeat als opmaat, maatsoort per sectie kiezen, occasionele 2/4- of 3/4-maat toelaten.
- Oorzaak halve zinnen: Whisper + difflib + naïeve lettergrepen. Oplossing: forced alignment van de exacte tekst (ctc-forced-aligner, MMS, taal fra, per regel; let op: modelgewichten CC-BY-NC), Franse e-muet-regel (gezongen als er een noot voor is), lettergreep-noot-toewijzing via dynamisch programmeren op klinkertijden.
- Kwaliteitscontrole: per maat een rapport "deze maten nakijken" (symbolische vergelijking met mir_eval, chroma-afstand origineel vs partituur, bereik/adem/maatlengte-controle met music21), met korte audiofragmenten.
- Tweede mening op zangnoten: GAME (openvpi, MIT), opvolger van SOME.
- Engraving: MuseScore 4 CLI of Verovio als alternatief/aanvulling op LilyPond.

## Werkversie 0.2 gebouwd (13/10/2026)
- Maatraster uit audio (Beat This! + DP op harmoniewissels): harmoniewissel op tel 1 in 51% (v0.1: 8%). 60 maten, waarvan 3x 2/4 en 1x 3/4 (opmaat). Tempo ~66.
- Beat This! sloeg in de intro tellen over (half tempo): tellen verdichten nodig.
- Tekst: forced alignment met Frans wav2vec2 (Apache-2.0, commercieel bruikbaar) i.p.v. MMS (CC-BY-NC). 226/226 woorden uitgelijnd; 95% binnen 0,3 s van een Suno-noot. 272 lettergrepen op een noot, 31 ontbrekende noten uit de zang toegevoegd (pyin).
- Bug gevonden en opgelost: noten sorteren op seconden én kwartnoten door elkaar schoof de zang op.
- Controlerapport per maat: zang 78% en piano 74% gelijk aan Suno-MIDI; 18 maten gemarkeerd.
- Dirk (musicus die verder werkt) gebruikt Finale: MusicXML aanleveren (Finale opent geen MuseScore-bestanden).
- Rebekka over v0.1: 30-40% juist, maar een vertrekpunt voor Dirk.
