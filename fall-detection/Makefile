# Fall-detection: binário único via PyInstaller (semelhante a `go build -o ...`).
#
# Diferença importante em relação ao Go: o executável tem de ser gerado NA MESMA
# família de SO do deploy (Linux x86_64/arm64, etc.). PyInstaller não faz
# cross-compile a partir do macOS para Linux — use uma VM Ubuntu ou CI Linux.
#
# Pré-requisito: venv com dependências do projeto + PyInstaller:
#   python3 -m venv .venv && . .venv/bin/activate
#   pip install -r requirements.txt && pip install -e . && pip install -r requirements-binary.txt

.PHONY: build clean-binary

build:
	pyinstaller --clean --noconfirm vigia-fall-detection.spec

clean-binary:
	rm -rf build dist/vigia-fall-detection
