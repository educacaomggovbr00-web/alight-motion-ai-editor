# Cache holds free dependencies only; all scripts are fresh.
FROM codex-resolve-deps
COPY dvip/source.py dvip/supervise.py dvip/edit_smoke.py dvip/internal_menu.py dvip/prepare_private_input.py dvip/private_input.py dvip/private_crypto.py /experiment/dvip/
