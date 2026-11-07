# vigia-lab — usa o .venv e o requirements.txt do vigia-onboard (nada próprio).
# Primeiro: `make -C ../vigia-onboard capture SETUP_ONLY=1` (cria o .venv) ou
# `py -3.13 -m venv ../vigia-onboard/.venv` + pip install -r ../vigia-onboard/requirements.txt

ifeq ($(OS),Windows_NT)
PY := ../vigia-onboard/.venv/Scripts/python.exe
else
PY := ../vigia-onboard/.venv/bin/python
endif

.PHONY: lab test provision

lab:           ## abre a interface para a Ana
	$(PY) -m vigia_lab

test:
	$(PY) -m pytest -q

provision:     ## make provision SRC=<pasta fall-classifier-bench>
	$(PY) scripts/provision_models.py --src "$(SRC)"
