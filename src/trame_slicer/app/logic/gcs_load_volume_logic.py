import logging
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote
from urllib.request import Request, urlopen

from trame_server import Server

from trame_slicer.core import SlicerApp

from ..ui import (
    GCSLoadVolumeState,
    GCSLoadVolumeUI,
)
from .base_logic import BaseLogic
from .load_volume_logic import LoadVolumeLogic

logger = logging.getLogger(__name__)


def get_gcs_download_url(bucket_name: str, gcs_path: str) -> str:
    encoded_bucket = quote(bucket_name, safe="")
    encoded_path = quote(gcs_path, safe="")

    return f"https://storage.googleapis.com/storage/v1/b/{encoded_bucket}/o/{encoded_path}?alt=media"


class GCSLoadVolumeLogic(BaseLogic[GCSLoadVolumeState]):
    def __init__(self, server: Server, slicer_app: SlicerApp, load_volume_logic: LoadVolumeLogic | None = None):
        super().__init__(server, slicer_app, GCSLoadVolumeState)
        self._load_volume_logic = (
            load_volume_logic if load_volume_logic is not None else LoadVolumeLogic(server, slicer_app)
        )

    def set_ui(self, ui: GCSLoadVolumeUI):
        ui.on_load_volume.connect(self._load_volume)

    def _load_volume(self, bucket_name: str, gcs_path: str, access_token: str) -> None:
        if not bucket_name or not gcs_path:
            logger.error("Bucket name and object path are required.")
            return

        with TemporaryDirectory() as tmp_dir:
            file_path = self._download_gcs_file(bucket_name, gcs_path, access_token, tmp_dir)
            if file_path is None:
                return

            self._slicer_app.scene.Clear()

            if file_path.endswith(".mrb"):
                self._load_volume_logic._on_load_scene(file_path)
            else:
                self._load_volume_logic._on_load_volume_files([file_path])

        self.data.dialog.is_open = False

    def _download_gcs_file(self, bucket: str, gcs_path: str, token: str, dest_dir: str) -> str | None:
        url = get_gcs_download_url(bucket, gcs_path)
        request = Request(url, headers={"Authorization": f"Bearer {token}"} if token else {})

        try:
            with urlopen(request) as response:
                dest = Path(dest_dir) / gcs_path.split("/")[-1]
                with dest.open("wb") as f:
                    shutil.copyfileobj(response, f)
                return str(dest)
        except Exception:
            logger.exception("Failed to download file from GCS: gs://%s/%s", bucket, gcs_path)
            return None
