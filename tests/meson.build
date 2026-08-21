# SPDX-License-Identifier: AGPL-3.0-or-later

test(
    'zfr-cli',
    py,
    args: [
        '-m',
        'unittest',
        'discover',
        '-s', meson.project_source_root() / 'tests',
        '-p',
        'test_*.py',
        '-v',
    ],
    workdir: meson.project_source_root(),
    env: [
        'PYTHONPATH=' + (meson.project_source_root() / 'tools'),
        'ZFR_PKGDATADIR=' + meson.project_source_root(),
        'NO_COLOR=1',
    ],
    timeout: 180,
)
