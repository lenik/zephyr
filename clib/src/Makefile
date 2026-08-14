# Run from repo root: make -C src organize-includes
# Or from : make organize-includes

SOURCES := $(shell find . -type f \( -name '*.c' -o -name '*.h' \) | sort)

.PHONY: format
format:
	organize-includes -n -I $(CURDIR) $(SOURCES)

bulk.h:
	grep -r -h '^#include <' | sort -u | grep -v bas/ >$@
