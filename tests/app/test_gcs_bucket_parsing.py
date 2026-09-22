from trame_slicer.app.logic.gcs_load_volume_logic import (
    GCSBucketItem,
    build_bucket_items,
)


def test_build_bucket_items_creates_folder_and_file_nodes():
    object_names = [
        "volume/brain/brain.nrrd",
        "volume/lung/lung.nrrd",
        "volume/lung/",
        "readme.txt",
    ]

    items = build_bucket_items(object_names)

    assert items == [
        GCSBucketItem(
            title="volume",
            value="volume",
            children=[
                GCSBucketItem(
                    title="brain",
                    value="volume/brain",
                    children=[GCSBucketItem(title="brain.nrrd", value="volume/brain/brain.nrrd", children=None)],
                ),
                GCSBucketItem(
                    title="lung",
                    value="volume/lung",
                    children=[GCSBucketItem(title="lung.nrrd", value="volume/lung/lung.nrrd", children=None)],
                ),
            ],
        ),
        GCSBucketItem(title="readme.txt", value="readme.txt", children=None),
    ]


def test_build_bucket_items_treats_trailing_slash_as_directory():
    items = build_bucket_items(["lung/", "brain/scan.nrrd"])
    assert items == [
        GCSBucketItem(
            title="brain",
            value="brain",
            children=[
                GCSBucketItem(title="scan.nrrd", value="brain/scan.nrrd", children=None),
            ],
        ),
        GCSBucketItem(title="lung", value="lung", children=[]),
    ]


def test_build_bucket_items_deduplicates_shared_prefixes():
    items = build_bucket_items(["a/b/c.txt", "a/b/d.txt"])
    assert items[0].title == "a"
    assert [c.title for c in items[0].children[0].children] == [
        "c.txt",
        "d.txt",
    ]
