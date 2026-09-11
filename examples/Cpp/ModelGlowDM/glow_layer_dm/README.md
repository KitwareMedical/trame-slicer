## Glow effect C++ code

### Requirements

Download a vtk-sdk wheel here: https://vtk.org/files/wheel-sdks/vtk-sdk/

/!\ vtk-sdk version has to be the same as the one specified in pyproject.toml

### Build wheel

```
cd examples/Cpp/ModelGlowDM/glow_layer_dm
pip wheel . -f /path/to/vtk_sdk.whl -w ./wheel
```

The final wheel will be created on ./wheel folder
