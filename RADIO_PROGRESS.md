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
