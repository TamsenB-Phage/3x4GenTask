# Variables
ENVS_DIR := conda_envs
ENV_SPEC := $(ENVS_DIR)/garmin-fit.yml
# The name of the environment is extracted from the .yml file
ENV_NAME := $(shell grep 'name:' $(ENV_SPEC) | cut -d' ' -f2)
# Sentinel file to track the last update
SENTINEL := $(ENVS_DIR)/.garmin-fit.sentinel

.PHONY: setup-all clean process comrades

# Default rule
setup-all: $(SENTINEL)

$(SENTINEL): $(ENV_SPEC)
	@echo "Checking if conda environment '$(ENV_NAME)' needs creation or update..."
	@if conda env list | grep -q "^$(ENV_NAME) "; then \
		echo "Updating existing environment: $(ENV_NAME)"; \
		conda env update --name $(ENV_NAME) --file $(ENV_SPEC) --prune; \
	else \
		echo "Creating new environment: $(ENV_NAME)"; \
		conda env create --file $(ENV_SPEC); \
	fi
	@echo "Installing modules in editable mode..."
	@conda run -n $(ENV_NAME) pip install -e .
	@touch $(SENTINEL)

clean:
	@echo "Removing sentinel file..."
	rm -f $(SENTINEL)

process:
	@conda run -n $(ENV_NAME) python -c "from preprocessing.orchestrator import run_global_orchestration; run_global_orchestration()"

comrades:
	@conda run -n $(ENV_NAME) python -c "import pandas as pd; \
	from preprocessing.orchestrator import run_global_orchestration; \
	from preprocessing.comrades_orchestrator import run_comrades_analysis; \
	df, _ = run_global_orchestration(); \
	run_comrades_analysis(df)"

report:
	@conda run -n $(ENV_NAME) python -c "\
from reporting.global_html_report import generate_training_report; \
generate_training_report('../out/master_workout_summary.tsv')"