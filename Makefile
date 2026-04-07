# --------------------------------------------------
# Environment configuration
# --------------------------------------------------

# Directory containing conda environment specifications
ENVS_DIR := conda_envs

# Path to the environment YAML file
ENV_SPEC := $(ENVS_DIR)/garmin-fit.yml

# Extract the environment name from the YAML file
# Assumes a line like: "name: garmin-fit"
ENV_NAME := $(shell grep 'name:' $(ENV_SPEC) | cut -d' ' -f2)

# Sentinel file used to track whether the environment has been
# created/updated since the last change to ENV_SPEC
SENTINEL := $(ENVS_DIR)/.garmin-fit.sentinel


# --------------------------------------------------
# Phony targets (not real files)
# --------------------------------------------------
.PHONY: setup-all clean process comrades report


# --------------------------------------------------
# Default target
# --------------------------------------------------

# Running `make` will trigger environment setup
setup-all: $(SENTINEL)


# --------------------------------------------------
# Environment setup logic
# --------------------------------------------------

# The sentinel depends on the environment spec file.
# If the YAML changes, this rule re-runs automatically.
$(SENTINEL): $(ENV_SPEC)
	@echo "Checking if conda environment '$(ENV_NAME)' needs creation or update..."

	# Check if environment already exists
	@if conda env list | grep -q "^$(ENV_NAME) "; then \
		echo "Updating existing environment: $(ENV_NAME)"; \
		conda env update --name $(ENV_NAME) --file $(ENV_SPEC) --prune; \
	else \
		echo "Creating new environment: $(ENV_NAME)"; \
		conda env create --file $(ENV_SPEC); \
	fi

	# Install project in editable mode (so local code changes are picked up immediately)
	@echo "Installing modules in editable mode..."
	@conda run -n $(ENV_NAME) pip install -e .

	# Touch sentinel to mark environment as up-to-date
	@touch $(SENTINEL)


# --------------------------------------------------
# Cleanup
# --------------------------------------------------

# Removes the sentinel file, forcing environment recreation/update on next run
clean:
	@echo "Removing sentinel file..."
	rm -f $(SENTINEL)


# --------------------------------------------------
# Data processing pipeline
# --------------------------------------------------

# Runs the full preprocessing orchestration pipeline
process:
	@conda run -n $(ENV_NAME) python -c "\
from preprocessing.orchestrator import run_global_orchestration; \
run_global_orchestration()"


# --------------------------------------------------
# Reporting
# --------------------------------------------------

# Generates the HTML training report from the processed summary file
report:
	@conda run -n $(ENV_NAME) python -c "\
from reporting.global_html_report import generate_training_report; \
generate_training_report('../out/master_workout_summary.tsv')"


# --------------------------------------------------
# Experimental
# --------------------------------------------------
recovery:
	@conda run -n $(ENV_NAME) python -c "\
from experiments.run_recovery_analysis import run_recovery_analysis; \
run_recovery_analysis('../out/master_workout_summary.tsv')"