# SPDX-License-Identifier: AGPL-3.0-or-later
"""Debian package build via build4 (local Docker or remote SSH).

Extracted from gh-makerelease's build_docker stage.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path


def prepare_build4_image(src: str) -> str:
    """Pull *src* and build a sibling ``*-build4`` image with empty ENTRYPOINT."""
    if ":" in src:
        name, tag = src.rsplit(":", 1)
    else:
        name, tag = src, "latest"
    dst = f"{name}:{tag}-build4"

    print(f"zfr package: preparing build4 image {dst} from {src}", flush=True)
    subprocess.run(["docker", "pull", src], check=False)
    # Interactive ENTRYPOINT ["/bin/bash","-i"] breaks build4's sh -c / argv form.
    dockerfile = f"FROM {src}\nENTRYPOINT []\n"
    build = subprocess.run(
        ["docker", "build", "-t", dst, "-"],
        input=dockerfile,
        text=True,
        check=False,
    )
    if build.returncode != 0:
        raise SystemExit(f"zfr package: could not prepare build4 image from {src}")
    return dst


def debian_build_inner(name: str, dpkg_buildopts: list[str], *, jobs: int = 1) -> str:
    opts_q = " ".join(shlex.quote(o) for o in dpkg_buildopts)
    if opts_q:
        opts_q += " "
    jobs = max(1, int(jobs))
    return f"""set -euo pipefail
cd {shlex.quote(name)}
export DEB_BUILD_OPTIONS="${{DEB_BUILD_OPTIONS:+$DEB_BUILD_OPTIONS }}parallel={jobs}"
if ! command -v debuild >/dev/null 2>&1 && ! command -v dpkg-buildpackage >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends build-essential debhelper devscripts dpkg-dev fakeroot
fi
if command -v mk-build-deps >/dev/null 2>&1 && [ -f debian/control ]; then
  mk-build-deps -i -r -t 'apt-get -y --no-install-recommends' || true
fi
if command -v debuild >/dev/null 2>&1; then
  debuild -j{jobs} {opts_q}
else
  dpkg-buildpackage -j{jobs} {opts_q}
fi"""


def build4_debian(
    projectdir: Path,
    *,
    base_image: str,
    dpkg_buildopts: list[str] | None = None,
    jobs: int = 1,
    dry_run: bool = False,
) -> None:
    """build4 mounts cwd at -w; cd to package parent and run from /workspace/<name>."""
    projectdir = projectdir.resolve()
    parent = projectdir.parent
    name = projectdir.name
    opts = list(dpkg_buildopts or [])
    jobs = max(1, int(jobs))

    if dry_run:
        print(f"+ prepare build4 image from {base_image}", flush=True)
        print(
            f"+ build4 -t <image>-build4 -w /workspace -- bash -lc <debuild -j{jobs}> (cwd={parent})",
            flush=True,
        )
        return

    if not shutil.which("build4"):
        raise SystemExit("zfr package: build4 not found (required for -d/--docker)")
    if not shutil.which("docker"):
        raise SystemExit("zfr package: docker not found (required for -d/--docker)")

    target = prepare_build4_image(base_image)
    print(f"zfr package: build4 target={target} (from {base_image}) package={name}", flush=True)

    inner = debian_build_inner(name, opts, jobs=jobs)
    build_cmd = f"bash -lc {shlex.quote(inner)}"
    cmd = ["build4", "-t", target, "-w", "/workspace", "--", build_cmd]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(parent), check=True)


def build4_debian_remote(
    projectdir: Path,
    *,
    docker_server: str,
    base_image: str,
    dpkg_buildopts: list[str] | None = None,
    jobs: int = 1,
    dry_run: bool = False,
) -> None:
    projectdir = projectdir.resolve()
    server = docker_server
    parent = projectdir.parent
    name = projectdir.name
    opts = list(dpkg_buildopts or [])
    jobs = max(1, int(jobs))

    print(f"zfr package: build4 remote ssh={server} base-image={base_image}", flush=True)
    if dry_run:
        print(f"+ ssh {server} mktemp / rsync / build4 -j{jobs} / fetch artifacts", flush=True)
        return

    if not shutil.which("rsync"):
        raise SystemExit("zfr package: rsync not found (required for -s/--docker-server)")

    try:
        remote_root = subprocess.check_output(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                server,
                "mktemp -d /tmp/zfr-package-XXXXXX",
            ],
            text=True,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"zfr package: could not create remote temp dir on {server}") from exc

    remote_parent = f"{remote_root}/work"
    remote_pkg = f"{remote_parent}/{name}"

    print(f"zfr package: remote workdir {server}:{remote_pkg}", flush=True)
    subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            server,
            f"mkdir -p {shlex.quote(remote_pkg)}",
        ],
        check=True,
    )
    rsync_push = [
        "rsync",
        "-a",
        "--delete",
        "--exclude",
        ".git/modules/",
        f"{projectdir}/",
        f"{server}:{remote_pkg}/",
    ]
    print("+", " ".join(rsync_push), flush=True)
    subprocess.run(rsync_push, check=True)

    build_inner = debian_build_inner(name, opts, jobs=jobs)
    build_cmd = f"bash -lc {shlex.quote(build_inner)}"

    remote_script = f"""set -euo pipefail
command -v build4 >/dev/null || {{ echo "build4 not found on {server}" >&2; exit 1; }}
command -v docker >/dev/null || {{ echo "docker not found on {server}" >&2; exit 1; }}
docker pull {shlex.quote(base_image)} || true
src={shlex.quote(base_image)}
if [[ "$src" == *:* ]]; then
  dst="${{src%:*}}:${{src##*:}}-build4"
else
  dst="${{src}}:latest-build4"
fi
printf 'FROM %s\\nENTRYPOINT []\\n' "$src" | docker build -t "$dst" -
cd {shlex.quote(remote_parent)}
build4 -t "$dst" -w /workspace -- {shlex.quote(build_cmd)}
"""
    remote = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", server, "bash", "-s"],
        input=remote_script,
        text=True,
        check=False,
    )
    if remote.returncode != 0:
        subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                server,
                f"rm -rf {shlex.quote(remote_root)}",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raise SystemExit(f"zfr package: remote build4 failed on {server}")

    rsync_pull = [
        "rsync",
        "-a",
        f"--include={name}_*.deb",
        f"--include={name}-*_*.deb",
        f"--include={name}_*.dsc",
        f"--include={name}_*.changes",
        f"--include={name}_*.buildinfo",
        f"--include={name}_*.tar.*",
        f"--include={name}_*.orig.tar.*",
        f"--include={name}_*.debian.tar.*",
        "--exclude=*",
        f"{server}:{remote_parent}/",
        f"{parent}/",
    ]
    print("+", " ".join(rsync_pull), flush=True)
    subprocess.run(rsync_pull, check=True)

    subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            server,
            f"rm -rf {shlex.quote(remote_root)}",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
