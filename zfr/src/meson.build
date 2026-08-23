# SPDX-License-Identifier: AGPL-3.0-or-later
# Installed PATH wrappers (PKGDATADIR = $prefix/share/zephyr).
foreach name : wrapper_names
    configure_file(
        input: name + '.in',
        output: name,
        configuration: inst_tool_cfg,
        install: true,
        install_dir: bindir,
        install_mode: 'rwxr-xr-x',
    )
endforeach
