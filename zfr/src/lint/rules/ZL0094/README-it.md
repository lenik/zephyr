# Versione progetto sostituita dalla config Meson e usata in almeno una sorgente

meson.build deve alimentare VERSION/PROJECT_VERSION via configuration_data (ize_cfg / config_h / paths_cfg), e almeno una sorgente sotto src/ (o un input configure_file) deve consumare @VERSION@ o PROJECT_VERSION.

### Sostituzione senza consumatore è incompleta

Meson deve sia definire VERSION/PROJECT_VERSION sia avere sorgenti che lo leggono davvero — altrimenti i binari pacchettizzati mentono ancora.


### Come viene controllato

Cerca chiavi configuration_data e uso di @VERSION@ / PROJECT_VERSION nelle sorgenti installate.


### Chiudere il cerchio

Aggiungete la metà mancante (subst o consumatore). Solve mappa ai passi ize subst quando disponibili.
