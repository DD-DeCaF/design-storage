.PHONY: setup network build start qa style safety test test-travis flake8 \
    isort isort-save license stop clean logs
SHELL:=/bin/bash

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Run all initialization targets.
setup: network databases

## Create the docker bridge network if necessary.
network:
	docker network inspect DD-DeCaF >/dev/null 2>&1 || \
		docker network create DD-DeCaF

## Create databases.
databases:
	docker-compose up -d postgres
	./scripts/wait_for_postgres.sh
	docker-compose exec postgres psql -U postgres -c "create database designs;"
	docker-compose exec postgres psql -U postgres -c "create database designs_test;"
	docker-compose run --rm web flask db upgrade
	docker-compose stop

## Build local docker images.
build:
	docker-compose build

## Recompile requirements and store pinned dependencies with hashes.
pip-compile:
	docker run --rm -v `pwd`/requirements:/build dddecaf/postgres-base:compiler \
		pip-compile --upgrade --generate-hashes \
		--output-file /build/requirements.txt /build/requirements.in

## Start all services in the background.
start:
	docker-compose up --force-recreate -d

## Run all QA targets.
qa: style safety test

## Run all style related targets.
style: flake8 isort license

## Run flake8.
flake8:
	docker-compose run --rm web \
		flake8 src/design_storage tests

## Check Python package import order.
isort:
	docker-compose run --rm web \
		isort --check-only --recursive src/design_storage tests

## Sort imports and write changes to files.
isort-save:
	docker-compose run --rm web \
		isort --recursive src/design_storage tests

## Verify source code license headers.
license:
	./scripts/verify_license_headers.sh src/design_storage tests

## Check for known vulnerabilities in python dependencies.
safety:
	docker-compose run --rm web safety check

## Run the tests.
test:
	docker-compose run --rm -e ENVIRONMENT=testing web \
		pytest --cov=src/design_storage

## Run the tests and report coverage (see https://docs.codecov.io/docs/testing-with-docker).
shared := /tmp/coverage
test-travis:
	mkdir --parents "$(shared)"
	docker-compose run --rm -e ENVIRONMENT=testing -v "$(shared):$(shared)" \
		web pytest --cov-report "xml:$(shared)/coverage.xml" --cov-report term \
		--cov=src/design_storage
	bash <(curl -s https://codecov.io/bash) -f "$(shared)/coverage.xml"

## Stop all services.
stop:
	docker-compose stop

## Stop all services and remove containers.
clean:
	docker-compose down

## Follow the logs.
logs:
	docker-compose logs --tail="all" -f

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := show-help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: show-help
show-help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
