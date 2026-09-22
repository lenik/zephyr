# Project version substituted by Meson config and used in at least one source

meson.build should feed VERSION/PROJECT_VERSION via configuration_data (ize_cfg / config_h / paths_cfg), and at least one source under src/ (or a configure_file input) must consume @VERSION@ or PROJECT_VERSION.

### Substitution without a consumer is incomplete

Meson must both define VERSION/PROJECT_VERSION and have sources that actually read it — otherwise packaged binaries still lie.


### How it is checked

Looks for configuration_data keys and for @VERSION@ / PROJECT_VERSION usage in installed sources.


### Closing the loop

Add the missing half (subst or consumer). Solve maps to the subst ize steps when available.
