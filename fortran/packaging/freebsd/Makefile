# Convenience targets for FreeBSD pkg (stub)
NAME    := zephyr
SRCDIR  := $(abspath ../..)
VERSION := $(shell cd "$(SRCDIR)" && { zfr version 2>/dev/null || head -n1 VERSION; })
VERSION := $(patsubst v%,%,$(strip $(VERSION)))

.PHONY: stage pkg clean

stage:
	cd "$(SRCDIR)" && meson setup build --prefix=/usr/local --buildtype=plain
	cd "$(SRCDIR)" && meson compile -C build
	rm -rf stage && mkdir -p stage
	cd "$(SRCDIR)" && DESTDIR="$(SRCDIR)/stage" meson install -C build

# TODO: generate + build pkg from stage + pkg-plist
pkg: stage
	@echo "TODO: pkg create from stage/ ($(NAME)-$(VERSION))"

clean:
	rm -rf "$(SRCDIR)/build" "$(SRCDIR)/stage"
