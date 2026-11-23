# Warder Radio Evolution — retencia vydaní (23.11.2026)

**Záväzné schválenie vlastníka:** aktuálna ostrá verzia + najviac tri staršie ostré verzie. TEST/RC nie sú ostré verzie. Staršie binárne Releases možno zmazať iba po preukázaní bezpečného prechodu všetkých podporovaných starých inštalácií, nulových aktívnych feed odkazov a zachovanej obnovy.

## Ostrá štvorica prehrávača

- `warder-radio-v0.2.2` — aktuálne
- `warder-radio-v0.2.1`
- `warder-radio-v0.2.0`
- `warder-radio-v0.1.9.4`

`update/v2/stable.json` aj `update/v2/testing.json` aktuálne smerujú na verifikované `0.2.2`. GitHub `main` nemá staré IPK v `packages/`, `dist/` alebo `build/`; sú len vo vydaniach alebo dočasných CI výstupoch.

**Nezameniteľná dátová výnimka:** `radio-country-20261122` je samostatné ostré vydanie 224 krajín (world bouquet + country PNG ZIPy) s aktívnym `assets/radio-country/latest.json`. NIE JE ďalším vydaním prehrávača, nesmie byť zahrnuté do číselnej retencie a jeho obsah sa nemení.

**Migrácia:** `warder-radio-v0.1.0-test11` je historický opkg bridge pre starú identitu a je stále citovaný vo vydávacom workflowe `.github/workflows/radio-test.yml`. Nemaž ho bez náhradnej reálne otestovanej migračnej cesty. Ostatné staré `0.1.9.2`, `0.1.9.3`, `0.2.0-test22` Releases čakajú na individuálne overenie externých odkazov a recovery kópií; ich existencia neznamená, že sú schválenými rollbackmi.

Zachovať obľúbené, históriu, nahrávky, nastavenia, externé originálne logá a otvorený [draft PR #52](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/pull/52). Nepridávať nové IPK do `main`. GitHub tag ani historický commit nemožno prepisovať. Preveriť CI pred každým zmazaním.

Spoločný aktuálny checkpoint: [FullHDGlass/docs/ECOSYSTEM-CLEANUP-CHECKPOINT-20261123.md](https://github.com/Evolution-by-Warder/FullHDGlass-Warder-Evolution/blob/main/docs/ECOSYSTEM-CLEANUP-CHECKPOINT-20261123.md).
