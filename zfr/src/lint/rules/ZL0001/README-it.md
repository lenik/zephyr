# Lunghezza del file sorgente; estrarre nella sottodirectory del pacchetto

### I file lunghi ostacolano l'ownership

File sorgente molto lunghi sono difficili da rivedere, testare e possedere. Zephyr preferisce moduli coesi — spesso sotto una sottodirectory di pacchetto con un file di ingresso sottile (la stessa forma che create/ize si aspettano). Una sottodirectory è opzionale: se gli helper sono esternalizzati altrimenti e il risultato resta manutenibile, va bene.


### Cosa guadagnate migliorando

Diff di revisione più piccoli, confini di modulo più chiari, test unitari più facili e meno conflitti di merge sui file molto toccati.


### Soglie

Lint conta le righe non vuote (saltando build/debian/po/…). Una nota compare intorno a ~600 righe; un avviso intorno a ~1000. I moduli di esempio dei template sono saltati. I percorsi che corrispondono a un `.lintignore` vicino (stile gitignore; può stare in qualsiasi sottodirectory) sono saltati — i template di linguaggio ignorano `*.css` per impostazione predefinita.


### La correzione è manuale

Spezzate o estraete sezioni coese e aggiornate voi stessi le liste meson/install/import. `zfr ize` non spezza automaticamente i sorgenti.
