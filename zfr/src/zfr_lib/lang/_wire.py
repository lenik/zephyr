# SPDX-License-Identifier: AGPL-3.0-or-later
"""Meson wiring helpers for zfr add / remove."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from .. import (
    append_meson_list_entry,
    case_variants,
    remove_meson_list_entry,
)
from ._spec import LangSpec, WireSpec


def append_man_custom_target(meson: Path, name: str) -> None:
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    if f"'{name}-man'" in text or f'"{name}-man"' in text:
        return
    block = f"""
custom_target(
    '{name}-man',
    input: 'docs/{name}.adoc',
    output: '{name}.1',
    command: [
        asciidoctor,
        '-b', 'manpage',
        '-a', 'project-version=' + meson.project_version(),
        '-a', 'project-year=@0@'.format(project_year),
        '-a', 'project-author=' + project_author,
        '-a', 'project-email=' + project_email,
        '-o', '@OUTPUT@',
        '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man1',
)
"""
    meson.write_text(text + block, encoding="utf-8")


def strip_man_custom_target(meson: Path, name: str) -> None:
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    new = re.sub(
        rf"\n?custom_target\(\n\s*'{re.escape(name)}-man',.*?\n\)\n",
        "\n",
        text,
        count=1,
        flags=re.S,
    )
    if new != text:
        meson.write_text(new, encoding="utf-8")


def strip_python_meson_puff(meson: Path, name: str) -> None:
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    original = text
    text = re.sub(
        rf"\n?{re.escape(name)}_exe = custom_target\(\n(?:.*?\n)*?\)\n",
        "\n",
        text,
        count=1,
    )
    text = re.sub(
        rf"\n?install_data\(\n\s*'{re.escape(name)}\.bash',\n(?:.*?\n)*?\)\n",
        "\n",
        text,
        count=1,
    )
    if text != original:
        meson.write_text(text, encoding="utf-8")
    strip_man_custom_target(meson, name)


def wire_add(spec: LangSpec, workdir: Path, name: str) -> None:
    wire = spec.wire
    meson = workdir / "meson.build"
    if wire.kind == "c":
        if not meson.is_file():
            return
        append_meson_list_entry(meson, wire.app_list, f"src/{name}.{wire.app_ext}")
        append_meson_list_entry(meson, wire.bash_list, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if wire.test_ext and tests_meson.is_file():
            append_meson_list_entry(tests_meson, "test_sources", f"{name}_test.{wire.test_ext}")
        if wire.man:
            append_man_custom_target(meson, name)
    elif wire.kind == "script":
        if not meson.is_file():
            return
        append_meson_list_entry(meson, wire.app_list, f"src/{name}.{wire.script_ext}")
        append_meson_list_entry(meson, wire.bash_list, f"{name}.bash")
        if wire.man:
            append_man_custom_target(meson, name)
    elif wire.kind == "python":
        if not meson.is_file():
            return
        text = meson.read_text(encoding="utf-8")
        if f"{name}_exe" not in text:
            block = f"""
{name}_exe = custom_target(
    '{name}',
    input: 'src/{name}.py',
    output: '{name}',
    command: [
        py,
        '-c',
        'import os, shutil, sys; shutil.copyfile(sys.argv[1], sys.argv[2]); os.chmod(sys.argv[2], 0o755)',
        '@INPUT@',
        '@OUTPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)
"""
            marker = "install_dir: bindir,\n)\n"
            idx = text.find(marker)
            if idx != -1:
                idx += len(marker)
                meson.write_text(text[:idx] + block + text[idx:], encoding="utf-8")
            else:
                insert_at = text.find("commons_mod = custom_target(")
                if insert_at == -1:
                    insert_at = text.find("install_data(")
                if insert_at == -1:
                    insert_at = len(text)
                meson.write_text(text[:insert_at] + block + "\n" + text[insert_at:], encoding="utf-8")
        text = meson.read_text(encoding="utf-8")
        if f"'{name}.bash'" not in text and f'"{name}.bash"' not in text:
            bash_block = f"""
install_data(
    '{name}.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: '{name}',
)
"""
            m = re.search(r"\ninstall_data\(\n\s*\[\n\s*'LICENSE'", text)
            if m:
                meson.write_text(text[: m.start()] + bash_block + text[m.start() :], encoding="utf-8")
            else:
                meson.write_text(text + bash_block, encoding="utf-8")
        append_man_custom_target(meson, name)
    elif wire.kind == "csharp":
        sln = workdir / "zephyr.sln"
        if sln.is_file():
            pascal = case_variants(name)["pascal"]
            text = sln.read_text(encoding="utf-8")
            if pascal not in text:
                guid = "{" + str(uuid.uuid4()).upper() + "}"
                line = (
                    f'Project("{{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}}") = '
                    f'"{pascal}", "apps/{name}/{pascal}.csproj", "{guid}"\n'
                    f"EndProject\n"
                )
                text = text.replace("\nGlobal\n", "\n" + line + "Global\n", 1)
                sln.write_text(text, encoding="utf-8")
        if wire.man:
            append_man_custom_target(meson, name)
    elif wire.kind == "go":
        pass
    elif wire.kind == "none" and wire.man:
        append_man_custom_target(meson, name)


def wire_remove(spec: LangSpec, workdir: Path, name: str) -> None:
    wire = spec.wire
    meson = workdir / "meson.build"
    if wire.kind == "c":
        if not meson.is_file():
            return
        remove_meson_list_entry(meson, f"src/{name}.{wire.app_ext}")
        remove_meson_list_entry(meson, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if wire.test_ext and tests_meson.is_file():
            remove_meson_list_entry(tests_meson, f"{name}_test.{wire.test_ext}")
        strip_man_custom_target(meson, name)
    elif wire.kind == "script":
        if not meson.is_file():
            return
        remove_meson_list_entry(meson, f"src/{name}.{wire.script_ext}")
        remove_meson_list_entry(meson, f"{name}.bash")
        strip_man_custom_target(meson, name)
    elif wire.kind == "python":
        strip_python_meson_puff(meson, name)
    elif wire.kind == "csharp":
        sln = workdir / "zephyr.sln"
        if sln.is_file():
            pascal = case_variants(name)["pascal"]
            text = sln.read_text(encoding="utf-8")
            new = re.sub(
                rf'Project\("[^"]+"\) = "{re.escape(pascal)}".*?\nEndProject\n',
                "",
                text,
                flags=re.S,
            )
            if new != text:
                sln.write_text(new, encoding="utf-8")
        strip_man_custom_target(meson, name)
    elif wire.man:
        strip_man_custom_target(meson, name)
