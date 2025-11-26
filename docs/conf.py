# Configuration file for the Sphinx documentation builder.

import sys
from pathlib import Path

from sphinx.ext import apidoc

import trame_slicer

cur_path = Path(__file__).parent

sys.path.insert(0, cur_path.parent.as_posix())

# -- Project information -----------------------------------------------------

project = "Trame Slicer"
copyright = "2025, Kitware"
author = "Kitware"

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.duration",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.mermaid",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for autodoc -----------------------------------------------------
autodoc_member_order = "bysource"
autodoc_mock_imports = ["slicer", "LayerDMLib", "vtkITK"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]

# -- Hooks for sphinx events -------------------------------------------------


def run_apidoc(*_):
    module_path = str(Path(trame_slicer.__file__).parent)
    output_dir = str(cur_path / "developer_guide")
    templates_path = str(cur_path / "apidoc_templates")

    argv = [
        "--force",
        "--module-first",
        "--output-dir",
        output_dir,
        "--templatedir",
        templates_path,
        module_path,
    ]

    apidoc.main(argv)


def setup(app):
    app.connect("builder-inited", run_apidoc)
