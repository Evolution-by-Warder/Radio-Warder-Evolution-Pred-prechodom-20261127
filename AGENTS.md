# Warder Radio – pokyny pre pokračovanie

## Trvalé pravidlo dokončovania schválenej práce (22. 11. 2026)

Toto pravidlo výslovne požadoval vlastník pre **všetky projekty Evolution-by-Warder**. Je nadradené starším všeobecným formuláciám o opakovanom schvaľovaní každého merge, IPK a produkčného zápisu.

1. **Jedno schválenie na konkrétny rozsah.** Ak vlastník schválil pomenovanú úpravu, celú dávku, vydanie alebo vopred definovanú automatickú aktualizáciu, súhlas zahŕňa aj obvyklé dokončovacie kroky v tomto rozsahu: vytvorenie PR, absolvovanie povinných testov, zlúčenie do `main`, zostavenie/vydanie príslušného finálneho balíka (ak projekt balíky vydáva) a aktualizáciu produkčného kanála. **Nepýtaj sa znovu na ten istý súhlas pri každom kroku ani v novom chate/Worku.** Rozsah a zdroj schválenia zapíš do PR a projektového denníka.
2. **Dokončenie po úspešnej verifikácii.** Pokiaľ rozsah zahŕňa produkčné vydanie a všetky povinné relevantné CI/regresné testy prejdú, bezpečne dokonči merge → release → verifikáciu skutočne publikovaného artefaktu/SHA-256 → aktualizáciu produkcie. Ak je nastavená schválená automatizácia, nech postup vykoná ona. Nevydávaj zbytočné medziverzie a nenechávaj hotové, schválené PR otvorené iba kvôli opakovanému žiadaniu.
3. **Žiadne neautorizované rozšírenie.** Test-only/draft, nová neschválená funkcia, zmena schválenej grafiky, neoverená licencia, zásah do súkromných dát, mazaní/zálohovaní či zmena autentifikácie nesmú byť ticho považované za schválené na produkciu. V týchto prípadoch si vyžiadaj jedno nové konkrétne schválenie.
4. **Povinné stop-podmienky.** Zlyhané alebo neúplné CI, zmena očakávaného SHA, nejasná identita artefaktu, konflikt vetvy, nedostatočné oprávnenia, bezpečnostná chyba alebo neoverená publikácia blokujú merge/vydanie. Skutočný stav a blokáciu zapíš; nikdy netvrď, že automatický merge či release prebehol, ak nie je doložený na GitHube.
5. **Trvalé odovzdanie.** Každý nový chat/Work načíta tieto pravidlá, aktuálny `main`, otvorené PR, CI, posledné vydanie a projektový register. Pokračuj od posledného overeného kroku a dokonči už schválenú prácu bez návratu na staré opakované schvaľovanie. Zachovaj používateľské súbory, existujúce schválené picony a históriu.

Toto je záväzné pravidlo práce vo všetkých repozitároch; **samo vloženie tohto textu nespúšťa GitHub automatizáciu**. Ak chýba mechanizmus automatického vykonania, odlíš pripravenú politiku od reálne aktivovaného workflowu.


- Tento repozitár spravuje samostatný plugin Warder Radio. Aktívny kandidát používa Radio Browser a online logá. Skin, satelitné picony, Vhannibal a spoločné šablóny patria do samostatného projektového Worku.
- Na začiatku nového chatu otvor [RADIO_PROGRESS.md](RADIO_PROGRESS.md) na aktívnej rádiovej vetve. Porovnaj zaznamenané SHA s aktuálnym `main` a dotknutými PR a vydaniami. Pokračuj od posledného doloženého kroku.
- Po každej významnej zmene aktualizuj register. Zapíš dátum, vetvu, SHA, rozsah testov, stav schválenia a publikácie a ďalší krok. Historické výsledky zostávajú v denníku a v odkazovaných checkpointoch.
- Rádiové balíky a príslušné PR v PiconHube sú archív predchádzajúcej implementácie. Aktívny vývoj online pluginu používa stránkovaný internetový katalóg a automatické logá. Pri aktualizácii chráň obľúbené, históriu, vlastné streamy, nastavenia, nahrávky a stiahnuté používateľské logá.
- Merge, publikovanie balíkov, vydanie IPK a zápis do produkcie vyžadujú preukázateľný súhlas s daným rozsahom; už udelený súhlas platí pre celý schválený vydávací cyklus bez opakovaných otázok. Rozlišuj lokálne testy, CI a fyzické overenie.

## Bezpečnosť prístupu a nahrávania na GitHub

- Používaj existujúce, používateľom autorizované GitHub pripojenie a jeho podporované operácie. Nemeň svojvoľne spôsob autentifikácie, neprihlasuj sa cez nový webový formulár, nevytváraj tokeny ani nežiadaj heslá, 2FA kódy či iné prihlasovacie tajomstvá.
- Ak existujúce pripojenie nestačí na nahratie veľkých binárnych súborov, zastav iba dotknutý prenos. Najprv zdokumentuj konkrétne obmedzenie, prípadnú chybu a bezpečné alternatívy; pred novou autentifikáciou alebo zmenou spôsobu prenosu vyžiadaj výslovný súhlas vlastníka.
- Bez nového súhlasu neskúšaj ďalšie prihlasovacie cesty, opakované Base64 uploady ani nekonečné opakovania zlyhávajúcej operácie. Ak je podporovaná už autorizovaná dávková cesta, použi ju iba v rámci existujúcich oprávnení a schváleného rozsahu.
- Pred zápisom over cieľovú vetvu, očakávaný obsah a SHA-256 existujúcich schválených súborov. Nečakaný rozdiel je blokácia, nie dôvod na prepísanie. Pracuj iba na oddelených pracovných vetvách; produkčný merge je dovolený po splnení CI v rozsahu predchádzajúceho výslovného schválenia podľa trvalého pravidla vyššie.
- Po každej bezpečne dokončenej dávke ulož commit a aktualizuj `RADIO_PROGRESS.md` s presným SHA, počtami, stavom úspešných uploadov a nespracovanými lokálnymi výstupmi. Nikdy neoznač lokálne pripravené archívy za nahrané, kým neoveríš ich existenciu a kontrolné súčty na GitHube.
