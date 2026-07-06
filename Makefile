.PHONY: help hooks dist formula-sha

help:
	@echo "claude-setup make targets:"
	@echo "  make hooks   install the pre-commit hook (git config core.hooksPath .githooks)"

hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit
	@echo "pre-commit hook installed: core.hooksPath -> .githooks"

VERSION := $(shell python3 -c "import clair; print(clair.__version__)")
DIST := dist/clair-$(VERSION).tar.gz

dist:
	@rm -rf dist && mkdir -p dist/clair-$(VERSION)
	@cp -R clair manifest.json home mboard install.sh LICENSE dist/clair-$(VERSION)/
	@find dist/clair-$(VERSION) -name '__pycache__' -type d -prune -exec rm -rf {} +
	@tar -C dist -czf $(DIST) clair-$(VERSION)
	@rm -rf dist/clair-$(VERSION)
	@shasum -a 256 $(DIST)
	@echo "dist: wrote $(DIST)"

# Compute the sha256 of the GitHub tag archive for Formula/clair.rb.
# Usage: make formula-sha VERSION=0.1.0   (defaults to clair.__version__)
formula-sha:
	@curl -fsSL "https://github.com/The007Programmer/clair/archive/refs/tags/v$(VERSION).tar.gz" \
		| shasum -a 256 | awk '{print $$1}'
