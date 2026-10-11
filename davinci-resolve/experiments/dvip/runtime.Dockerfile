# Only open-source dependencies are cached; scripts are copied fresh.
FROM codex-resolve-deps
COPY dvip/source.py dvip/supervise.py dvip/edit_smoke.py dvip/internal_menu.py /experiment/dvip/
