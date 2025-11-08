# Recipe Robot Makefile

# Variables
XCODE_WORKSPACE = app/Recipe Robot.xcworkspace
SCHEME = Recipe Robot
BUILD_DIR = build
PYTHON = /usr/local/autopkg/python

# Default target
.PHONY: help
help: ## Show available targets
	@echo "Recipe Robot Build System"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Dependencies
.PHONY: deps
deps: ## Update Carthage dependencies
	cd app && carthage update --platform macOS

# Testing
.PHONY: test
test: test-python test-xcode ## Run all tests (Python and Xcode)

.PHONY: test-python
test-python: ## Run Python unit tests
	$(PYTHON) -m coverage run -m unittest discover -vs scripts

.PHONY: test-xcode
test-xcode: deps ## Run Xcode app tests
	xcodebuild test -workspace "$(XCODE_WORKSPACE)" \
		-scheme "$(SCHEME)" \
		-destination 'platform=macOS'

.PHONY: test-coverage
test-coverage: ## Run tests with coverage
	$(PYTHON) -m coverage html
	$(PYTHON) -m coverage xml
	$(PYTHON) -m coverage report

# Building
.PHONY: archive
archive: ## Archive the app for distribution
	@mkdir -p $(BUILD_DIR)
	xcodebuild -workspace "$(XCODE_WORKSPACE)" \
		-scheme "$(SCHEME)" \
		-configuration Release \
		-archivePath "$(BUILD_DIR)/Recipe Robot.xcarchive" \
		archive

# Utilities
.PHONY: clean
clean: ## Clean build artifacts
	rm -rf $(BUILD_DIR)
	rm -rf htmlcov
	rm -rf scripts/**/__pycache__

.PHONY: open
open: ## Open Xcode workspace
	open "$(XCODE_WORKSPACE)"
