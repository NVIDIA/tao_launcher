all: build install

build:
	python3 release/tao/setup.py bdist_wheel

clean:
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -rf **/*/__pycache__

install: build
	pip3 install dist/nvidia_tao-*.whl

uninstall:
	pip3 uninstall -y nvidia-tao
	pip3 uninstall -y -r dependencies/requirements-pip.txt