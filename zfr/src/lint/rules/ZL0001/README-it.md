# Lunghezza del file sorgente; estrai nella sottodirectory del pacchetto

### I file lunghi combattono per la proprietà

I file di origine molto lunghi sono difficili da revisionare, testare e gestire. Zephyr preferisce moduli coesi — spesso sotto una sottodirectory del pacchetto con un file di punto di ingresso sottile (la stessa struttura che create/ize si aspetta). Una sottodirectory è opzionale: se gli helper sono esternalizzati in un altro modo e il risultato è mantenibile, va bene.


### Cosa ti dà migliorarne

Revisioni più piccole, confini dei moduli più chiari, test unitari più facili e meno conflitti di unione sui file occupati.


### Soglie

Lint conta le righe non vuote (saltando build/debian/po/…). Una nota appare intorno alle ~600 righe; un avviso intorno alle ~1000. I moduli di esempio del modello vengono saltati. I percorsi che corrispondono a un `.lintignore` nelle vicinanze (stile gitignore; può trovarsi in qualsiasi sottodirectory) vengono saltati — i modelli di linguaggio includono `*.css` ignorati per default.


### La riparazione è manuale

Dividi o estrai sezioni coerenti e aggiorna tu stesso le liste meson/install/import. `zfr ize` non suddivide automaticamente le sorgenti.
