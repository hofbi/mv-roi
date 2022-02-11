test: unit_test integration_test

format:
	shfmt -l -w .

check:
	shfmt -d .

.PHONY: unit_test
unit_test:
	python3 -m unittest

.PHONY: integration_test
integration_test:
	python3 -m unittest discover -p "*_test.py"

coverage:
	coverage run --branch --omit=venv/*,test/* -m unittest
	coverage run --branch --omit=venv/*,test/* --append -m unittest discover -p "*_test.py"
	coverage report -m

coverage_reports: coverage
	coverage xml
	coverage html

## Setup
BDDA_PATH = bdda/driver_attention_prediction

setup:
	pip3 install -r requirements.txt

setup_bdda: .setup_bdda_common .setup_mvroi
	cd docker && docker-compose build

setup_bdda_venv: .setup_bdda_common .setup_mvroi
	sudo apt install -y python3-venv ffmpeg
	python3 -m venv bdda/venv

.setup_bdda_common:
	git submodule update --init
	models="pretrained_models.zip" && \
	  wget -nc -P $(BDDA_PATH) --no-check-certificate 'https://docs.google.com/uc?export=download&id=1q_CgyX73wrYTAsZjDF9aMXNPURcUmWVy' -O $$models && \
	  unzip -u -d $(BDDA_PATH) $$models && \
	  rm $$models
	wget -P $(BDDA_PATH) https://www.cs.toronto.edu/~guerzhoy/tf_alexnet/bvlc_alexnet.npy

.setup_mvroi:
	unzip bdda/weights/MV-ROI.zip
