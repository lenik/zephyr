# SPDX-License-Identifier: AGPL-3.0-or-later
i18n = import('i18n')

# zfr: i18n-derive-begin
_po_src = meson.current_source_dir()
_po_build = meson.current_build_dir()
_sh = find_program('sh')
_po_dep_list = run_command(
  _sh, '-c', 'cd "$1" && ls -1 *.po LINGUAS 2>/dev/null || true',
  _po_src, check: false,
).stdout().strip().split('\n')
_po_dep_files = []
foreach _p : _po_dep_list
  if _p != ''
    _po_dep_files += [_p]
  endif
endforeach

_zfr_py = find_program('python3', native: true)
_zfr_cli = meson.project_source_root() / 'src' / 'zfr'
_i18n_env = environment()
_i18n_env.set('PYTHONPATH', meson.project_source_root() / 'src')
_i18n_env.set('ZFR_PKGDATADIR', meson.project_source_root())

custom_target(
  'i18n-derive',
  command: [
    _zfr_py, _zfr_cli, 'i18n', '-b',
    '--po-dir', _po_build,
    '--stamp', '@OUTPUT@',
    '--compile-mo',
    '--domain', 'zfr',
  ],
  output: 'i18n-derive.stamp',
  depend_files: _po_dep_files,
  env: _i18n_env,
  build_by_default: true,
  console: true,
)
# zfr: i18n-derive-end

i18n.gettext(
    'zfr',
    data_dirs: _po_src,
    install: true,
    # Install under the usual share/locale; runtime looks at ZFR_LOCALEDIR / system.
)
