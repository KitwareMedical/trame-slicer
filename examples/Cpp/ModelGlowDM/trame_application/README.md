## Glow layer DM Python application

### Description

A simple trame-slicer application that uses a custom layerDM with a glow effect
on actors using C++ classes.

### Requirements

#### glow_layer_dm.whl

See examples/Cpp/ModelGlowDM/glow_layer_dm/README.md

#### Virtual environment

```
python3.12 -m venv ./venv
source ./venv/bin/activate
```

### Install

```
cd trame_application
pip install -r requirements.txt
pip install path/to/glow_layer_dm/wheel/glow_layer_dm-1.0.0-...whl

python ./custom_layer_dm_app.py
```
