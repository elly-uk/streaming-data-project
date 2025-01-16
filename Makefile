.PHONY: create-environment requirements build-lambda test coverage lint security run clean check deploy destroy help 

# Variables
PIP = venv/bin/pip
PYTHON := python3
ACTIVATE_ENV = source venv/bin/activate

# Define utility variable to help calling Python from the virtual environment
define execute_in_env
	$(ACTIVATE_ENV) && $1
endef

# Create virtual environment
create-environment:
	@echo ">>> About to create environment..."
	@echo ">>> check python version"
	( \
		$(PYTHON) --version; \
	)
	@echo ">>> Setting up VirtualEnv."
	( \
		$(PYTHON) -m venv venv; \
	)

# Install requirements
requirements: create-environment
	$(call execute_in_env, $(PIP) install pip-tools)
	$(call execute_in_env, $(PIP) install -r requirements.txt)

# Build AWS Lambda package
build-lambda:
	rm -rf lambda_package
	mkdir -p lambda_package
	$(call execute_in_env, $(PIP) install -r requirements.txt -t lambda_package)
	cp src/lambda_function.py lambda_package/
	cd lambda_package && zip -r ../lambda_function.zip ./*

# Run tests
test:
	$(call execute_in_env, $(PYTHON) -m pytest --testdox tests/)

# Run tests with coverage
coverage:
	$(call execute_in_env, $(PYTHON) -m pytest --testdox --cov=src --cov-report=term-missing --cov-report=html tests/)

# Check code style (PEP-8 compliance)
lint:
	$(call execute_in_env, $(PYTHON) -m flake8 src tests)
	@echo "Linting completed successfully!"

# Run security checks
security:
	$(call execute_in_env, $(PYTHON) -m bandit -r src)

# Run the application
run: build-lambda
	$(call execute_in_env, $(PYTHON) src/lambda_function.py)

# Clean up (remove virtual environment and other artifacts)
clean:
	rm -rf venv
	rm -rf lambda_package
	rm -f lambda_function.zip
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf .vscode
	find . -type d -name "__pycache__" -exec rm -r {} +

	rm -rf terraform/.terraform
	rm -f terraform/.terraform.lock.hcl
	rm -f terraform/terraform.tfstate
	rm -f terraform/terraform.tfstate.backup

# Meta-target for combined checks
check: lint security test
	@echo "All checks passed!"

# Deploy the application
deploy: 
	cd terraform && terraform init && terraform plan && terraform apply

# Destroy the deployment
destroy:
	cd terraform && terraform destroy

# Display help
help:
	@echo "Available commands:"
	@echo "  create-environment - Create virtual environment"
	@echo "  requirements - Install requirements"
	@echo "  build-lambda - Build AWS Lambda package"
	@echo "  test - Run tests"
	@echo "  coverage - Run tests with coverage report"
	@echo "  lint - Check code style (PEP-8 compliance)"
	@echo "  security - Run security checks"
	@echo "  run - Run the application"
	@echo "  clean - Remove all generated files"
	@echo "  check - Run lint, security, and test"
	@echo "  deploy - Deploy the application to AWS Lambda"
	@echo "  destroy - Destroy the application on AWS Lambda"
	@echo "  help - Show this help message"