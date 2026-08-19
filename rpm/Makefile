# Convenience targets for local RPM builds.
#
# Usage (from rpm/):
#   make srpm    # source RPM
#   make rpm     # binary RPM
#
# Version comes from `zephyr version` (same as meson.build).

NAME    := zephyr
SRCDIR  := $(abspath ..)
TOPDIR  ?= $(abspath $(SRCDIR)/rpmbuild)

# Version via `zephyr version` (git describe / changelog / VERSION / 0.0.0).
# zephyr is expected on PATH; fall back to VERSION then 0.0.0.
VERSION := $(shell cd "$(SRCDIR)" && { zephyr version 2>/dev/null || true; })
ifeq ($(strip $(VERSION)),)
VERSION := $(shell head -n1 "$(SRCDIR)/VERSION" 2>/dev/null)
endif
VERSION := $(patsubst v%,%,$(strip $(VERSION)))
ifeq ($(strip $(VERSION)),)
VERSION := 0.0.0
endif
RPM_VERSION := $(shell cd "$(SRCDIR)" && { zephyr version -r 2>/dev/null || true; })
ifeq ($(strip $(RPM_VERSION)),)
RPM_VERSION := $(subst -,_,$(VERSION))
endif

TARBALL := $(NAME)-$(VERSION).tar.xz
DISTDIR := $(TOPDIR)/tmp/$(NAME)-$(VERSION)

# Debian rpmbuild cannot satisfy RPM BuildRequires from dpkg packages.
RPMBUILD_FLAGS :=
ifneq ($(wildcard /etc/debian_version),)
RPMBUILD_FLAGS += --nodeps
endif

TAR_EXCLUDES := \
	--exclude='./build' \
	--exclude='./rpmbuild' \
	--exclude='./.git' \
	--exclude='./.cache' \
	--exclude='./.cursor' \
	--exclude='./.vscode' \
	--exclude='./debian/build' \
	--exclude='./debian/zephyr' \
	--exclude='./debian/.debhelper' \
	--exclude='./debian/files'

.PHONY: all dist spec srpm rpm clean version

all: rpm

version:
	@echo $(VERSION)

dist:
	rm -rf $(TOPDIR)/tmp
	mkdir -p $(TOPDIR)/SOURCES $(TOPDIR)/SPECS $(DISTDIR)
	tar -C $(SRCDIR) $(TAR_EXCLUDES) -cf - . | tar -C $(DISTDIR) -xf -
	tar -C $(TOPDIR)/tmp -cJf $(TOPDIR)/SOURCES/$(TARBALL) $(NAME)-$(VERSION)
	rm -rf $(TOPDIR)/tmp

# Freeze versions into the spec so SRPM rebuilds do not fall back to 0.0.0.
spec: dist $(NAME).spec
	mkdir -p $(TOPDIR)/SPECS
	{ \
		printf '%s\n' \
			'%global version $(RPM_VERSION)' \
			'%global srcversion $(VERSION)' \
			''; \
		cat $(NAME).spec; \
	} > $(TOPDIR)/SPECS/$(NAME).spec

srpm: spec
	mkdir -p $(TOPDIR)/SRPMS
	rpmbuild $(RPMBUILD_FLAGS) \
		-D "_topdir $(TOPDIR)" \
		-bs $(TOPDIR)/SPECS/$(NAME).spec

rpm: spec
	mkdir -p $(TOPDIR)/BUILD $(TOPDIR)/RPMS
	rpmbuild $(RPMBUILD_FLAGS) \
		-D "_topdir $(TOPDIR)" \
		-bb $(TOPDIR)/SPECS/$(NAME).spec

clean:
	rm -rf $(TOPDIR)
