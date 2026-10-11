"""Importa um ZIP do checkout para o editor Remotion.

ATENCAO: ao enviar este ZIP a um repositorio publico o video tambem fica
publico e pode permanecer no historico Git apos a exclusao do arquivo.
Para midia privada, prefira usar secret-zip em repositorio privado.
"""
from pathlib import Path
from download_input import extract


def main():
    root = Path("importar/entrada.zip")
    if not root.is_file() or root.is_symlink():
        raise SystemExit(
            "Arquivo nao encontrado: remotion-emo-rap/importar/entrada.zip. "
            "Faca upload do ZIP com esse nome, ou selecione entrada=demo."
        )
    if root.stat().st_size > 450 * 1024 ** 2:
        raise SystemExit("ZIP excede limite de 450 MiB")
    extract(root, Path("public/input"))
    print("ZIP importado do checkout: video, audio original e JSONs preparados")


if __name__ == "__main__":
    main()
