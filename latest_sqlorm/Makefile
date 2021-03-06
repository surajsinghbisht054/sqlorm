# Some useful commands to create a simple readme page with mkdocs.


help:
	@echo 'Usage: make [command]'
	@echo 'Commands:'
	@echo '  env          Create an isolated development environment.'
	@echo '  deps         Install dependencies.'
	@echo '  build        Create a dist package.'
	@echo '  install      Install a local dist package with pip.'
	@echo '  clean        Remove all Python, test and build artifacts.'
	@echo '  clean-build  Remove build artifacts.'
	@echo '  clean-pyc    Remove Python file artifacts.'
	@echo '  clean-test   Remove test and coverage artifacts.'

env:
	virtualenv env && . env/bin/activate && make deps

deps:
	test -f requirements.txt && \
	pip install -r requirements.txt || echo "requirements.txt doesn't exists"

build:
	python setup.py egg_info sdist bdist_wheel
	ls -l dist

install: build
	pip install dist/*.tar.gz

clean: clean-pyc clean-test clean-build

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .cache/
	rm -fr .tox/
	rm -fr htmlcov/
	rm -f .coverage
