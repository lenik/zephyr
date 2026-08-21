# Convenience targets for local RPM builds.
#
# Usage (from rpm/):
#   make srpm    # source RPM
#   make rpm     # binary RPM
#
# Version comes from `zfr version` (same as meson.build).
# Dist reuses `zfr dist --rpm` (meson dist at the git root, else a
# project-only tarball for nested language templates). Extra flags:
#   make dist DIST_FLAGS='-b /other/build'

NAME    := zephyr
SRCDIR  := $(abspath ..)
TOPDIR  ?= $(abspath $(SRCDIR)/rpmbuild)
DIST_FLAGS ?=

# Version via `zfr version` (git describe / changelog / VERSION / 0.0.0).
# zfr is expected on PATH; fall back to VERSION then 0.0.0.
VERSION := $(shell cd "$(SRCDIR)" && { zfr version 2>/dev/null || true; })
ifeq ($(strip $(VERSION)),)
VERSION := $(shell head -n1 "$(SRCDIR)/VERSION" 2>/dev/null)
endif
VERSION := $(patsubst v%,%,$(strip $(VERSION)))
ifeq ($(strip $(VERSION)),)
VERSION := 0.0.0
endif
RPM_VERSION := $(shell cd "$(SRCDIR)" && { zfr version -r 2>/dev/null || true; })
ifeq ($(strip $(RPM_VERSION)),)
RPM_VERSION := $(subst -,_,$(VERSION))
endif

# Debian rpmbuild cannot satisfy RPM BuildRequires from dpkg packages.
RPMBUILD_FLAGS :=
ifneq ($(wildcard /etc/debian_version),)
RPMBUILD_FLAGS += --nodeps
endif

.PHONY: all dist spec srpm rpm clean version

all: rpm

version:
	@echo $(VERSION)

# Prefer source-tree tools/zephyr (meta-repo bootstrap); else zfr on PATH.
dist:
	mkdir -p $(TOPDIR)/SOURCES $(TOPDIR)/SPECS
	@set -e; \
	cd "$(SRCDIR)"; \
	if [ -f tools/zephyr ]; then \
		python3 tools/zfr dist --rpm -o "$(TOPDIR)/SOURCES" $(DIST_FLAGS); \
	elif command -v zfr >/dev/null 2>&1; then \
		zfr dist --rpm -o "$(TOPDIR)/SOURCES" $(DIST_FLAGS); \
	else \
		echo "zfr dist: zfr not found on PATH" >&2; \
		exit 1; \
	fi

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
