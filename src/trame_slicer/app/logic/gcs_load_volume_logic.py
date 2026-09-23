import asyncio
import logging
from json import JSONDecodeError, load
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

import aiohttp
from slicer import vtkMRMLVolumeNode
from trame_server import Server
from undo_stack import Signal

from trame_slicer.core import SlicerApp

from ..ui import (
    GCSBucketItem,
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


def get_gcs_list_url(bucket_name: str) -> str:
    encoded_bucket = quote(bucket_name, safe="")
    return f"https://storage.googleapis.com/storage/v1/b/{encoded_bucket}/o"


def build_bucket_items(object_names: list[str]) -> list[GCSBucketItem]:
    bucket_items: list[GCSBucketItem] = []

    for name in object_names:
        parts = name.split("/")
        parent = bucket_items
        prefix = ""
        for index, part in enumerate(parts):
            if parent is None or not part:
                continue

            prefix = f"{prefix}/{part}" if prefix else part
            is_directory = index < len(parts) - 1

            # Search for existing item in the current parent
            item = next((child for child in parent if child.value == prefix), None)

            if item is None:
                item = GCSBucketItem(title=part, value=prefix, children=[] if is_directory else None)
                parent.append(item)

            parent = item.children

    return _sort_bucket_items(bucket_items)


def _sort_bucket_items(items: list[GCSBucketItem]) -> list[GCSBucketItem]:
    items.sort(key=_item_sort_key)
    for item in items:
        if item.children is not None:
            item.children = _sort_bucket_items(item.children)
    return items


def _item_sort_key(item: GCSBucketItem) -> tuple[bool, str]:
    return (item.children is None, item.title.lower())


class GCSLoadVolumeLogic(BaseLogic[GCSLoadVolumeState]):
    volume_loaded = Signal(vtkMRMLVolumeNode)

    def __init__(
        self,
        server: Server,
        slicer_app: SlicerApp,
        load_volume_logic: LoadVolumeLogic | None = None,
        gcs_bucket_name: str | None = None,
    ):
        super().__init__(server, slicer_app, GCSLoadVolumeState)
        if load_volume_logic is not None:
            self._load_volume_logic = load_volume_logic
        else:
            self._load_volume_logic = LoadVolumeLogic(server, slicer_app)
            self._load_volume_logic.volume_loaded.connect(self.volume_loaded)

        if gcs_bucket_name:
            self.data.is_dialog_open = True
            self._browse_bucket(gcs_bucket_name)

    def set_ui(self, ui: GCSLoadVolumeUI):
        ui.on_browse_bucket.connect(self._browse_bucket)
        ui.on_load_volume.connect(self._load_volume)

    def _list_bucket_objects(self, bucket: str) -> list[str]:
        names = []

        url = f"{get_gcs_list_url(bucket)}"
        with urlopen(url) as response:
            data = load(response)

            names.extend(item["name"] for item in data.get("items", []))

        return names

    def _browse_bucket(self, bucket_name: str) -> None:
        if not bucket_name:
            return

        try:
            object_names = self._list_bucket_objects(bucket_name)
            self.data.bucket_connected = True
            self.data.bucket_name = bucket_name
            self.data.bucket_browse.bucket_items = build_bucket_items(object_names)
            self.data.bucket_browse.selected_items = []

        except (HTTPError, URLError) as err:
            self.data.bucket_connected = False
            logger.exception("Network or HTTP error listing bucket %s: %s", bucket_name, err)

        except JSONDecodeError as err:
            self.data.bucket_connected = False
            logger.exception("Failed to parse JSON response from bucket %s: %s", bucket_name, err)

        except KeyError as err:
            self.data.bucket_connected = False
            logger.exception("Unexpected response structure from bucket %s: missing %s", bucket_name, err)

    async def _download_gcs_file(
        self, session: aiohttp.ClientSession, bucket: str, gcs_path: str, dest_dir: str
    ) -> str | None:
        url = get_gcs_download_url(bucket, gcs_path)
        dest = Path(dest_dir) / gcs_path.split("/")[-1]

        async with session.get(url) as response:
            response.raise_for_status()
            with dest.open("wb") as f:
                while chunk := await response.content.read(64 * 1024):
                    f.write(chunk)
            return str(dest)

    async def _load_volume(self, selected_paths: list[str]) -> None:
        if not self._typed_state.data.bucket_name or not selected_paths:
            return

        try:
            connector = aiohttp.TCPConnector(limit=30)
            with TemporaryDirectory() as tmp_dir:
                async with aiohttp.ClientSession(connector=connector) as session:
                    tasks = [
                        self._download_gcs_file(session, self._typed_state.data.bucket_name, path, tmp_dir)
                        for path in selected_paths
                    ]
                    # Download all requested files concurrently
                    results = await asyncio.gather(*tasks)

                downloaded_files = [f for f in results if f is not None]

                if not downloaded_files:
                    return

                self._slicer_app.scene.Clear()

                if len(downloaded_files) == 1 and downloaded_files[0].endswith(".mrb"):
                    self._load_volume_logic._on_load_scene(downloaded_files[0])
                else:
                    self._load_volume_logic._on_load_volume_files(downloaded_files)

                self.data.is_dialog_open = False

        except aiohttp.ClientResponseError as err:
            logger.exception("GCS HTTP status error (%s) downloading files: %s", err.status, err.message)

        except aiohttp.ClientError as err:
            logger.exception("Network connection failure during GCS download: %s", err)

        except OSError as err:
            logger.exception("File system write error saving downloaded files: %s", err)

        except RuntimeError as err:
            logger.exception("Slicer core failed to parse/load volume files: %s", err)

        finally:
            self.data.bucket_browse.loading_busy = False
            self.state.flush()
