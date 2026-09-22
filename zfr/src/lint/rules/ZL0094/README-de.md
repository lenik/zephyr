# Projektversion durch Meson-Config ersetzt und in mindestens einer Quelle genutzt

meson.build soll VERSION/PROJECT_VERSION über configuration_data (ize_cfg / config_h / paths_cfg) speisen, und mindestens eine Quelle unter src/ (oder eine configure_file-Eingabe) muss @VERSION@ oder PROJECT_VERSION verbrauchen.

### Substitution ohne Verbraucher ist unvollständig

Meson muss VERSION/PROJECT_VERSION sowohl definieren als auch Quellen haben, die es wirklich lesen — sonst lügen gepackte Binaries weiterhin.


### Wie geprüft wird

Sucht configuration_data-Schlüssel und @VERSION@ / PROJECT_VERSION-Nutzung in installierten Quellen.


### Den Kreis schließen

Die fehlende Hälfte ergänzen (Subst oder Verbraucher). Solve mappt auf die Subst-ize-Schritte, wenn verfügbar.
