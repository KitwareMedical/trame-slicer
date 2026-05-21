from __future__ import annotations

from pathlib import Path

from trame.app.file_upload import ClientFile


def write_client_files_to_dir(
    client_file_dicts: list[dict],
    dest_dir: str | Path,
) -> list[str]:
    """
    Helper method to copy files from client to a local server dir
    """
    file_list = []
    dest_dir = Path(dest_dir)
    for file in client_file_dicts:
        file_helper = ClientFile(file)
        file_path = dest_dir / file_helper.name
        file_path.write_bytes(file_helper.content)
        file_list.append(file_path.as_posix())
    return file_list
