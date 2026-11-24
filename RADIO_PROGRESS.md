## 24. 11. 2026 — Uzavretý historický REVIEW #52

Na pokyn vlastníka uzavretý #52 bez merge konfliktného historického REVIEW. Ostré vydanie 0.2.2 (#53), produkčný katalóg 224 krajín / 48 219 staníc / 40 837 PNG (#54) a automatické aktualizácie 1. a 15. deň (#55) sú v main. Historická vetva a výsledky zostávajú zachované, neopakovať spracované dávky. Prvý úplný plánovaný cyklus ešte neoverený; pri ďalšom behu riešiť iba skutočné zmeny. Žiadny nový IPK.

## 22. 11. 2026 — HOTOVÉ: 224-krajinné rádio v ostrej produkcii + schválené pravidelné automatické aktualizácie

- **Všetkých 224 krajín a 48 219 staníc** (40 837 originálnych rádiových PNG) je v ostrom dátovom vydaní [radio-country-20261122](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/releases/tag/radio-country-20261122). Všetkých 225 nemenných súborov ostalo pôvodných, s presnou SHA-256/veľkosťou: world ZIP 6 664 493 B, SHA `771953b41ceab46f8852f5e3219338cb1369d7f653ed7d329ad551e481f88d68`; celkom 835 703 250 B. Oficiálny feed `main/assets/radio-country/latest.json` bol publikovaný až po kontrole, [workflow #45036963424 SUCCESS](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/actions/runs/45036963424), PR #54 zlúčený.
- **Bez opakovania alebo rozrastania inštalačného IPK**: celosvetové logá sú samostatne na serveri, skin používa malý svetový bouquet a len originálne ZIP logá aktívnej krajiny na externom úložisku. Stabilná samostatná verzia prehrávača `Warder Radio 0.2.2` zostáva Latest.
- **Dvojtýždňová serverová automatizácia** pre 1. a 15. deň v mesiaci: [PR #55](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/pull/55) zlúčený, merge `e1df53b6b429bf2dd9631b6582212d830e072d8e`. Workflowy `radio-world-all-bouquets-review.yml`, `radio-country-fortnightly-logos-review.yml`, `publish-radio-country-fortnightly.yml`: znovu prejdú 224 krajín, originálne rádiové logá, presné UUID/SHA, odmietnu neúplné zdroje a pokles počtu existujúcich originálov, pripravia a vydajú iba zmenené country ZIPy, nezmenené odkazujú na predošlé nemenné vydania. `latest.json` sa zmení až po overenom vydaní. Žiadny receiver nezíska svetový 836MB archív cez plugin IPK.
- **Podrobný bazálny index** 224 krajín s per-country bouquet/catalogue SHA a `logo_attempted/logos_found/logos_missing` doplnený na `main/assets/radio-country/latest.json` bez zmeny identít alebo pôvodných ZIP: [workflow #45038829355 SUCCESS](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/actions/runs/45038829355). Staré aj nové záznamy umožňujú bezpečné SHA-dedup plánovanie.
- **CI**: testy automatizačných workflowov, nezávislé regrese a PR validácie SUCCESS (#45038692259, #45038692169, #45038692148, #45038044425, #45038039862). Nový plán sa aktivuje pri nasledujúcej dátumovo plánovanej udalosti; prvý celý živý automatický cyklus ešte nebol vykonaný. Fyzické testovanie na konkrétnom prijímači je samostatné.
- Skin FullHDGlass produkčné prepojenie na `main/assets/radio-country/latest.json` pripravené ako `v1.0.83` v [PR #133](https://github.com/Evolution-by-Warder/FullHDGlass-Warder-Evolution/pull/133), zatiaľ sa testuje/nesmie sa označiť ako publikované pred CI a vydaním.

---

# Warder Radio 0.2.2 – OSTRÉ VYDANIE 22. novembra 2026

- **Vlastník výslovne schválil ostré vydanie.** [PR #53](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/pull/53) je zlúčený do `main`, merge commit `739901e9fa2691ecdaddbe4460133a76360a5c2e`. Zdroj obsahuje päť bezpečne oddelených runtime modulov pre vyhľadávanie a ochranu online originálnych log staníc.
- **Oficiálna ostrá verzia `0.2.2-1` bola vydaná:** [GitHub Release warder-radio-v0.2.2](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/releases/tag/warder-radio-v0.2.2), [vydávací GitHub Actions #45034367710 SUCCESS](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/actions/runs/45034367710). Verejný IPK `enigma2-plugin-extensions-radio-warder-evolution_0.2.2_all.ipk`, presne **2 946 582 B**, SHA-256 **`1378757cca0a87c9a1ec2712817185f42aa1754b165509d50803c19dd7d1f08e`**. Reálny balík aj SHA256SUMS boli nezávisle prevzaté zo súborov oficiálneho publikujúceho runu a overené po bajtoch.
- **Produkčné aktualizačné zdroje aktualizované:** `update/v2/stable.json` aj `update/v2/testing.json` teraz ponúkajú overenú `0.2.2` s rovnakou URL, SHA a veľkosťou; publikujúce workflow overilo verejný download pred posunom feedov. Produkčný feed commit `4817e13c70140c8978d698c76589615ff604a0c6`.
- **Testy:** finálny súkromný kandidát [#45033656828 SUCCESS](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/actions/runs/45033656828), plná PR validácia [#45033656813 SUCCESS](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/actions/runs/45033656813). Natívne OpenATV 8.0/8.1, OpenPLi 9.2, full unit tests a skutočná offline aktualizácia cez opkg `0.2.1-1→0.2.2-1` aj reinštalácia PASS, šesť vzorových používateľských súborov bajtovo zachovaných. Oficiálne publikujúce workflow zvlášť úspešne absolvovalo build, unit/native testy, živé overenie obalov skladieb a úplné vydanie.
- **Rozsah:** Nová ochrana zdrojov rádiových log, overené fallbacky a rozšírené spracovanie originálnych online obrázkov; celý 224-krajinný svetový ZIP a viac ako 40-tisíc cudzích station-brand obrázkov nie sú zabalené do tejto IPK, nehrozí ich zápis do internej flash touto aktualizáciou. Obľúbené, história, vlastné streamy, nastavenia, cache, nahrávky zostávajú vlastníctvom používateľa.
- **Samostatná nevydaná oblasť:** [PR #52](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/pull/52) s 224 krajinami, 48 219 stanicami a 225 kompletne SHA overenými TEST assetmi zostáva **DRAFT/TEST**, nie distribúcia pre produkciu. Práva redistribúcie cudzích log, produkčný index, dlhodobá automatizácia a fyzické overenie priamo na prijímači zostávajú samostatnou bránou; vydanie 0.2.2 ich neautorizuje.
- **Fyzické overenie ostrej 0.2.2 na konkrétnom prijímači** nie je potvrdené a nemožno ho zamieňať za automatické CI.

---

## 22. 11. 2026 — Warder Radio 0.2.2 standalone runtime candidate (TEST, not public stable)

- **Actual latest official stable:** `0.2.1`, released [warder-radio-v0.2.1](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/releases/tag/warder-radio-v0.2.1). Prior 0.2.0-only entry below is retained as historical context.
- **Separated exactly five reviewed online-radio-logo runtime modules** from [world-review PR #52](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/pull/52), without its 836MB third-party country-logo world. Isolated draft [PR #53](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/pull/53) branches from current stable main; version prepared as `0.2.2-1`. No country ZIP in binary, no source overwrites of previous Radio Browser/favourites/history/player.
- [Independent 0.2.2 full candidate CI #45033293070 SUCCESS](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/actions/runs/45033293070). Real IPK `enigma2-plugin-extensions-radio-warder-evolution_0.2.2_all.ipk`, **2 946 582 B**, **SHA-256 `1378757cca0a87c9a1ec2712817185f42aa1754b165509d50803c19dd7d1f08e`**. Actual control `Version: 0.2.2-1`, 142 data members, no global world file. Artifact contains IPK, `SHA256SUMS`, unit/native/opkg logs; bytes independently downloaded and locally verified.
- CI: **187 unit cases PASS, 14 intentionally skipped optional/integration cases**; 88 native tests each for OpenPLi 9.2, OpenATV 8.1 and OpenATV 8.0; **real offline opkg stable 0.2.1-1 → 0.2.2-1 and reinstall PASS**; six representative user-controlled files (saved settings, favourites, history, custom picons, recording) byte-identical after the upgrade. Additional CairoSVG-enabled regression run is configured to exercise the optional vector renderer rather than relying on skipped tests.
- **Outstanding:** physical receiver evaluation and explicit user authorization before merging PR #53 or publishing `0.2.2` stable. PR #52's 224 country original-logo bundles are independent and remain test-only pending rights/redistribution signoff and production index release. Never confuse test artwork with a stable logo distribution.
- No changes to `main`, stable update feeds, public release tags, approved packages or user files from this candidate branch.

---

# Radio Warder Evolution – stav stabilného vydania

## 0.2.0 Stable

Oficiálne stabilné vydanie: [warder-radio-v0.2.0](https://github.com/Evolution-by-Warder/Radio-Warder-Evolution/releases/tag/warder-radio-v0.2.0).

Podporované funkcie: Radio Browser, Domov, Odbery, Obľúbené, História, vyhľadávanie, prehrávanie streamov, ICY metadáta, online logá staníc s obmedzenou cache, albumové obaly, texty piesní, informácie o interpretoch, nahrávanie, YouTube a OLED šetrič.

- Stabilná vetva `main` má verziu 0.2.0.
- Online logá sú priebežne získavané len pre relevantné viditeľné stanice.
- Používateľské dáta pod `/etc/enigma2/warder-radio` zostávajú zachované.
- Testy OpenATV 8.0, OpenATV 8.1 a OpenPLi 9.2 a aktualizácie pomocou opkg prešli pri vydaní.

Ďalšie zmeny nesmú bez výslovného schválenia upravovať stabilnú verziu ani vydávací kanál.
