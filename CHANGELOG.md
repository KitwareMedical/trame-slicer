# CHANGELOG

<!-- version list -->

## v1.8.0 (2026-02-09)

### Bug Fixes

- **dataclass_proxy**: Return None for other node types
  ([`0b4a88f`](https://github.com/KitwareMedical/trame-slicer/commit/0b4a88f305ec388cd4322806fe470b68b6aa9fc0))

### Chores

- Add parallel test execution
  ([`e1ff161`](https://github.com/KitwareMedical/trame-slicer/commit/e1ff161aa2886abf02afd514d304c0b880f1d363))

- Force changelog update
  ([`cdf8f80`](https://github.com/KitwareMedical/trame-slicer/commit/cdf8f80ad207b9bcd3c0a0db0cd79bf585fa04e7))

- Update semantic release config
  ([`b3eb4c7`](https://github.com/KitwareMedical/trame-slicer/commit/b3eb4c7ba1cd1841c249f83dda94349fe3edc8e7))

### Documentation

- **examples**: Add minimal trame slicer app
  ([`c54fad0`](https://github.com/KitwareMedical/trame-slicer/commit/c54fad0476d145510bdf06dcaf425290a61624a7))

### Features

- **abstract_view**: Add access to displayable manager
  ([`737a721`](https://github.com/KitwareMedical/trame-slicer/commit/737a721693a53aca15b901b9b684e79b9cb45f7c))

- **io_manager**: Add write volume
  ([`c1ebafe`](https://github.com/KitwareMedical/trame-slicer/commit/c1ebafefb47ff61eea49eb3d4356f07a9d42e732))

- **segmentation**: Add segment border thickness control
  ([`411001d`](https://github.com/KitwareMedical/trame-slicer/commit/411001d8f2c46f2f1d77175a097bac0155739b6b))

- **volumes**: Add volume display presets
  ([`284c445`](https://github.com/KitwareMedical/trame-slicer/commit/284c445d944b7a56c8bfb15072e278f00af3127f))

### Refactoring

- **ui**: Move example SliderState to trame_slicer.ui
  ([`138ec6f`](https://github.com/KitwareMedical/trame-slicer/commit/138ec6fa7d87e6343903bd030218c615d8c73e28))

### Testing

- Fix test_abstract_view
  ([`fe66c59`](https://github.com/KitwareMedical/trame-slicer/commit/fe66c5962ff87fff620eac8a5bc47a585cc59b1a))


## Unreleased

### Bug Fixes

- **dataclass_proxy**: Return None for other node types
  ([`0b4a88f`](https://github.com/KitwareMedical/trame-slicer/commit/0b4a88f305ec388cd4322806fe470b68b6aa9fc0))

### Chores

- Add parallel test execution
  ([`e1ff161`](https://github.com/KitwareMedical/trame-slicer/commit/e1ff161aa2886abf02afd514d304c0b880f1d363))

- Update semantic release config
  ([`b3eb4c7`](https://github.com/KitwareMedical/trame-slicer/commit/b3eb4c7ba1cd1841c249f83dda94349fe3edc8e7))

### Documentation

- **examples**: Add minimal trame slicer app
  ([`c54fad0`](https://github.com/KitwareMedical/trame-slicer/commit/c54fad0476d145510bdf06dcaf425290a61624a7))

### Features

- **io_manager**: Add write volume
  ([`c1ebafe`](https://github.com/KitwareMedical/trame-slicer/commit/c1ebafefb47ff61eea49eb3d4356f07a9d42e732))

- **segmentation**: Add segment border thickness control
  ([`411001d`](https://github.com/KitwareMedical/trame-slicer/commit/411001d8f2c46f2f1d77175a097bac0155739b6b))

- **volumes**: Add volume display presets
  ([`284c445`](https://github.com/KitwareMedical/trame-slicer/commit/284c445d944b7a56c8bfb15072e278f00af3127f))

### Refactoring

- **ui**: Move example SliderState to trame_slicer.ui
  ([`138ec6f`](https://github.com/KitwareMedical/trame-slicer/commit/138ec6fa7d87e6343903bd030218c615d8c73e28))

### Testing

- Fix test_abstract_view
  ([`fe66c59`](https://github.com/KitwareMedical/trame-slicer/commit/fe66c5962ff87fff620eac8a5bc47a585cc59b1a))


## v1.7.2 (2025-12-17)

### Bug Fixes

- **rca_view**: Fix rca side effect with vtkWindowToImageFilter
  ([`d72a0d7`](https://github.com/KitwareMedical/trame-slicer/commit/d72a0d7e309227a59eb539ded8292d9acf8fba1b))

- **views**: Fix registration of builtin displayable managers
  ([`b07b3d4`](https://github.com/KitwareMedical/trame-slicer/commit/b07b3d45d83a3c2975c4f7bdf8556c20e354d6df))


## v1.7.1 (2025-12-11)

### Bug Fixes

- **examples**: Fix examples for Slicer trame
  ([`88d9d16`](https://github.com/KitwareMedical/trame-slicer/commit/88d9d165423fd2cb4a748591bab52c6fccea9ce3))


## v1.7.0 (2025-12-09)

### Bug Fixes

- **seg**: Trigger modified on undo and redo operations
  ([`34b3481`](https://github.com/KitwareMedical/trame-slicer/commit/34b3481602a420f057f612ef3fb25a78166ffdb6))

- **segmentation_effect_threshold**: Reduce blink refresh rate
  ([`82128f1`](https://github.com/KitwareMedical/trame-slicer/commit/82128f19c34bb77617873dcdef3e8f093713be70))

### Chores

- Activate test CI
  ([`8ddad98`](https://github.com/KitwareMedical/trame-slicer/commit/8ddad98bbcb1746dc81b3b19699fc0c82e852e09))

- Add CI code coverage upload
  ([`4bef881`](https://github.com/KitwareMedical/trame-slicer/commit/4bef8812301ebe16ceb9fd57339bc609296a52eb))

### Documentation

- Fix read the docs generation
  ([`86fd515`](https://github.com/KitwareMedical/trame-slicer/commit/86fd515e30734e7e694c093b82d96aeeb31f4556))

- Improve documentation
  ([`e3963f6`](https://github.com/KitwareMedical/trame-slicer/commit/e3963f60a6a58e8c9ffcd5ed96212831abcece08))

- **example**: Add directory load button in example
  ([`a2bb411`](https://github.com/KitwareMedical/trame-slicer/commit/a2bb4116354881908c4a116983a622baaf587ae1))

- **example**: Use VFileInput for file inputs
  ([`44a991e`](https://github.com/KitwareMedical/trame-slicer/commit/44a991e34923a2907044f8bb10407d57d790e423))

- **examples**: Add segmentation example app
  ([`9ede25a`](https://github.com/KitwareMedical/trame-slicer/commit/9ede25a2599f5df459df4f95452debd58721c4e0))

- **readme**: Add turbo-jpeg installation note to README
  ([`55f8813`](https://github.com/KitwareMedical/trame-slicer/commit/55f8813515b64a0fb8078956f8b3104ca807667e))

### Features

- **segmentation**: Add island segmentation
  ([`e60a649`](https://github.com/KitwareMedical/trame-slicer/commit/e60a6491afa242c4061181e19d88fe92547cec34))

- **segmentation**: Add undo command grouping
  ([`2730273`](https://github.com/KitwareMedical/trame-slicer/commit/27302735bf9d08e4d0670f733e46c93e6f028734))

### Refactoring

- Remove unused utils files
  ([`c5c0453`](https://github.com/KitwareMedical/trame-slicer/commit/c5c0453c00d7f422c13974c866422c19a1c98aa2))


## v1.6.3 (2025-11-15)

### Bug Fixes

- Fix cursor offset in views
  ([`ef8670c`](https://github.com/KitwareMedical/trame-slicer/commit/ef8670cbba83cf8294b520448fc30ff306b52da3))


## v1.6.2 (2025-11-07)

### Bug Fixes

- **threshold_effect**: Fix threshold undo/redo
  ([`0a9786f`](https://github.com/KitwareMedical/trame-slicer/commit/0a9786f00e427d21207a7c8609519eea84eb7f48))


## v1.6.1 (2025-11-07)

### Bug Fixes

- Fix import for Slicer trame
  ([`5e57b47`](https://github.com/KitwareMedical/trame-slicer/commit/5e57b476fed1f4e494c787d859f409cb6d91fa4e))


## v1.6.0 (2025-11-06)

### Features

- **segmentation**: Add threshold effect
  ([`3257017`](https://github.com/KitwareMedical/trame-slicer/commit/3257017c65978088afe8de0e7b57e0071c9d34d8))


## v1.5.1 (2025-11-04)

### Bug Fixes

- **view_manager**: Fix mpr interaction not working after scene load
  ([`1aa013a`](https://github.com/KitwareMedical/trame-slicer/commit/1aa013aaf09dde7a4fcc3e37d2cf597e043487f3))

- **views**: Fix default render window multi samples
  ([`3845258`](https://github.com/KitwareMedical/trame-slicer/commit/3845258b9f41e6300a1251b1670ce34b924318f5))

- **views**: Fix reset camera to use screen space
  ([`a2d915d`](https://github.com/KitwareMedical/trame-slicer/commit/a2d915d50cdbaa2c69e4ed8b01fc188bbe0f3376))

### Documentation

- **examples**: Add scene loading in medical viewer example
  ([`6ceed5e`](https://github.com/KitwareMedical/trame-slicer/commit/6ceed5ed1d1048dffc66d06c9fadf5ee3e2a65f0))


## v1.5.0 (2025-10-27)

### Bug Fixes

- Fix application behavior on scene clear
  ([`40c054d`](https://github.com/KitwareMedical/trame-slicer/commit/40c054dce0e8a81e9c4bec9d51b7cc50dbf6769b))

### Documentation

- Update wheels link
  ([`dd1dffa`](https://github.com/KitwareMedical/trame-slicer/commit/dd1dffacdb5471278b4ef7f23326e2d59b9d0b28))

### Features

- **views**: Add api to hide volumes
  ([`44650ec`](https://github.com/KitwareMedical/trame-slicer/commit/44650eca48756e67235921d200eee77b9cc7bc31))

- **volume_rendering**: Add toggle roi node visibility
  ([`df10daf`](https://github.com/KitwareMedical/trame-slicer/commit/df10daf32eea99436fa78697f656f6b5ba3b3ea5))

- **volume_rendering**: Add VR opacity setting
  ([`6d00ead`](https://github.com/KitwareMedical/trame-slicer/commit/6d00eade5e949d26f96f85d5ab128e23a396b2a2))


## v1.4.0 (2025-10-23)

### Bug Fixes

- Fix application crash on switching volume
  ([`bc3533c`](https://github.com/KitwareMedical/trame-slicer/commit/bc3533c83fca59a80fac609342ab2000bed49749))

- **layout_manager**: Fix layout manager compatibility with child server pattern
  ([`a1f6a5f`](https://github.com/KitwareMedical/trame-slicer/commit/a1f6a5ff81c2fa962290ec06a6d93e38e8625e8d))

- **layout_manager**: Fix layout manager initialization
  ([`b8c2c88`](https://github.com/KitwareMedical/trame-slicer/commit/b8c2c88e2e1b7c2e9f5e0d90052e098f676c3faa))

- **layout_manager**: Fix layout manager virtual node
  ([`41cfaed`](https://github.com/KitwareMedical/trame-slicer/commit/41cfaed2ef7b0dd116a45762e98997dadd684248))

- **views**: Fix cross hair compatibility
  ([`f1d7bec`](https://github.com/KitwareMedical/trame-slicer/commit/f1d7becf038834786de369de4d937ac69bdf6080))

### Documentation

- Update download documentation
  ([`e8cf769`](https://github.com/KitwareMedical/trame-slicer/commit/e8cf7694afba0af7343d8f0fd452a2bcac624175))

- Update technical debt
  ([`f64e1b8`](https://github.com/KitwareMedical/trame-slicer/commit/f64e1b89509d1d8d881a2e957a2b40c4cb347da5))

### Features

- **rca_view**: Add cursor forwarding
  ([`667a98b`](https://github.com/KitwareMedical/trame-slicer/commit/667a98bc297f305fbd3a9aeaeb692ca17572afed))

- **segmentation**: Segmentation refactoring
  ([`38c78b2`](https://github.com/KitwareMedical/trame-slicer/commit/38c78b2e0b908082f9b8b6a6f7001ca5a9981753))

- **slicer_app**: Module logic registration mechanism
  ([`725392a`](https://github.com/KitwareMedical/trame-slicer/commit/725392a3701858506970d2b3053ee50f67f5afac))

### Refactoring

- Add modified event for SlicerWrapper
  ([`51d93d5`](https://github.com/KitwareMedical/trame-slicer/commit/51d93d59bbb6e963352a9940862313ed84275849))

- Move segmentation display to dedicated class
  ([`7815914`](https://github.com/KitwareMedical/trame-slicer/commit/7815914811ed167fb89cd72241496d92633f3415))

- Remove tests/data from gitignore
  ([`60c70b7`](https://github.com/KitwareMedical/trame-slicer/commit/60c70b743ecc071d3b8a89a0691e1eb6975c91c1))

- Remove vtk event dispatcher
  ([`2452657`](https://github.com/KitwareMedical/trame-slicer/commit/245265763ab5df7c54e4e257f60f3cdbb4bc7bdb))

### Testing

- Add test data as git submodule
  ([`7f0f3c0`](https://github.com/KitwareMedical/trame-slicer/commit/7f0f3c0d5727f24ebdbcc092e8d902650338a244))

- Add timeout for tests with async playwright
  ([`61df75a`](https://github.com/KitwareMedical/trame-slicer/commit/61df75a47139ee68b3a3bbc74461670be444e511))

- Test layout manager with child servers
  ([`5fe432a`](https://github.com/KitwareMedical/trame-slicer/commit/5fe432a3d7aa8f004f34ea2fdeb1a46e47237869))

- Update medical example test
  ([`ebcb898`](https://github.com/KitwareMedical/trame-slicer/commit/ebcb89836a02ea3e36d56b39aad905b3e344e794))

- Update tests to playwright
  ([`cd96236`](https://github.com/KitwareMedical/trame-slicer/commit/cd96236b914bcdbe549e089b60f853fd439c8666))


## v1.3.0 (2025-09-29)

### Features

- **rca_view**: Add event throttle and compression
  ([`be53e0f`](https://github.com/KitwareMedical/trame-slicer/commit/be53e0f23d2fb3ff9e759c9887f35eef86583823))

- **view_manager**: Add support for non Slicer view types
  ([`b88106d`](https://github.com/KitwareMedical/trame-slicer/commit/b88106d6a54a7efbe6fa2c8e275306525f4ef105))


## v1.2.0 (2025-09-15)

### Bug Fixes

- **segmentation**: Add validity checks to display node getters in segmentation
  ([`d286ed5`](https://github.com/KitwareMedical/trame-slicer/commit/d286ed53fbb4d13dd2dc84c026421ea4126d25ab))

- **views**: Render slice views on foreground opacity change
  ([`6155258`](https://github.com/KitwareMedical/trame-slicer/commit/615525842f0a4a297aa2366dddee241d72abc885))

### Chores

- Change release to workflow_dispatch
  ([`b5a39cc`](https://github.com/KitwareMedical/trame-slicer/commit/b5a39cc83e8a25f9554fb09a021de5361381f676))

### Features

- **views**: Enable blend rendering of two volumes in 2D views
  ([`83228c8`](https://github.com/KitwareMedical/trame-slicer/commit/83228c84b1d311ab22383ce7479814c89930c8f4))


## v1.1.0 (2025-08-07)

### Bug Fixes

- **view_layout_definition**: Add missing layout color to properties
  ([`c5353ae`](https://github.com/KitwareMedical/trame-slicer/commit/c5353ae106e0e70d37d413534308885f5399717d))

### Chores

- Update dependencies for the library
  ([`f827ce3`](https://github.com/KitwareMedical/trame-slicer/commit/f827ce37ed7c3d17637f0b45268eed5a0e41b520))

- **gh-action**: Add dry-run semantic release
  ([`58bc243`](https://github.com/KitwareMedical/trame-slicer/commit/58bc243114fe8499487f7322c00383943e24e06c))

### Documentation

- Add technical debt and architecture design docs
  ([`a24fcbb`](https://github.com/KitwareMedical/trame-slicer/commit/a24fcbbe3ad5542079c6dbd2bb8dd964538f4920))

### Features

- **views**: Add block rendering
  ([`b63d075`](https://github.com/KitwareMedical/trame-slicer/commit/b63d075ff61a5e56a4ce75676aa5eed8c1d4ea2a))

- **views**: Add thick slab reconstruction
  ([`b176246`](https://github.com/KitwareMedical/trame-slicer/commit/b176246a0f703a61112470845d37163ddfdf4461))

- **views**: Factorize displayable manager init
  ([`03fa63f`](https://github.com/KitwareMedical/trame-slicer/commit/03fa63f44d573c53de738a3b0ab605bb92caa680))

- **views**: Improve RCA render performance
  ([`5f0e1dc`](https://github.com/KitwareMedical/trame-slicer/commit/5f0e1dc5fd7ccb3238a31195243ed624378619f7))

- **volume_rendering**: Add crop_logic property
  ([`9cb26a9`](https://github.com/KitwareMedical/trame-slicer/commit/9cb26a9d93a8faff452a094c0a9882e9ccd968d2))

### Refactoring

- **views**: Refactor expected view types to enums
  ([`b0e1567`](https://github.com/KitwareMedical/trame-slicer/commit/b0e156704a693bdc57433be74799ee219c66614a))


## v1.0.0 (2025-06-18)

### Documentation

- Update README.md with grant references
  ([`904d46e`](https://github.com/KitwareMedical/trame-slicer/commit/904d46efabd82572bca6d27cc1636af663e8480a))


## v0.7.1 (2025-05-20)

### Bug Fixes

- **segmentation**: Fix scissors effect for python 3.9
  ([`0e28b3e`](https://github.com/KitwareMedical/trame-slicer/commit/0e28b3e6a54eb78660bf8ea673119436063d65b9))

- **views**: Fix slice views default tag
  ([`96e5f1e`](https://github.com/KitwareMedical/trame-slicer/commit/96e5f1e6a8a7208fc1a94b9c925d4937ed7f4101))


## v0.7.0 (2025-05-15)

### Code Style

- Update format line length
  ([`3c0f912`](https://github.com/KitwareMedical/trame-slicer/commit/3c0f912ca6f130d62a9a2ca05d785ece368f7459))

### Features

- **python-version**: Add support for Python 3.9
  ([`b90e449`](https://github.com/KitwareMedical/trame-slicer/commit/b90e449a98de40e7179701d6cab061243dce70d1))


## v0.6.0 (2025-05-07)

### Bug Fixes

- **views**: Fix 3d picking logic
  ([`727f77f`](https://github.com/KitwareMedical/trame-slicer/commit/727f77fa5564d7d5468689f49e65c3474c6a434c))

### Features

- **core**: Add markups logic
  ([`4dce7ba`](https://github.com/KitwareMedical/trame-slicer/commit/4dce7ba556fb724bcd9c1825047bc11ca9f8f8bc))


## v0.5.0 (2025-04-29)

### Bug Fixes

- **segmentation**: Fix wrong segmentation typehints
  ([`015d43e`](https://github.com/KitwareMedical/trame-slicer/commit/015d43ef7baf362e97042af64fd9f2de87520c68))

### Chores

- **pre-commit**: Add commit lint rule
  ([`0ebbfc4`](https://github.com/KitwareMedical/trame-slicer/commit/0ebbfc4b94bfa1f1930c418e86da2b6b3bc98be8))

### Features

- **segmentation**: Add segments visibility control
  ([`af7f1bc`](https://github.com/KitwareMedical/trame-slicer/commit/af7f1bceb228b09a56deefda97f7c75713ef8a6a))


## v0.4.0 (2025-04-24)

### Bug Fixes

- **typing**: Fix load_dcm_volumes return typing
  ([`75dc5e2`](https://github.com/KitwareMedical/trame-slicer/commit/75dc5e2be80fa0d2421038b16962063051ccf249))

### Chores

- **CHANGELOG**: Enable back change log
  ([`730c52f`](https://github.com/KitwareMedical/trame-slicer/commit/730c52f44741fd78ad30983929bc9f85a52471f8))

### Features

- **view_manager**: Add filter access on visible layout views
  ([`4d1091d`](https://github.com/KitwareMedical/trame-slicer/commit/4d1091d8475efa413a8339e3e67d12b7c80e1580))

- **volume_rendering**: Add volume ROI crop
  ([`05e91b8`](https://github.com/KitwareMedical/trame-slicer/commit/05e91b8541148fc11f65793cabe1c83784480b7e))

- **volume_window_level**: Add Window/Level
  ([`3c3a6f5`](https://github.com/KitwareMedical/trame-slicer/commit/3c3a6f57b84564aa702a4b60ef9d07f6f11601df))


## v0.3.0 (2025-04-23)

### Features

- **segmentation**: Add segment opacity control
  ([`8f9a084`](https://github.com/KitwareMedical/trame-slicer/commit/8f9a08463dc362cda711065914fbae0e206a685d))


## v0.2.2 (2025-04-23)

### Bug Fixes

- **segmentation**: Fix non-opaque 3D segments transparency
  ([`651553f`](https://github.com/KitwareMedical/trame-slicer/commit/651553f05e8fd1319d213d5862a29d64a5eeadd0))


## v0.2.1 (2025-04-23)

### Bug Fixes

- **slice_view**: Fix fit to content
  ([`a60f792`](https://github.com/KitwareMedical/trame-slicer/commit/a60f79264acfa0af63b594bf66381914b1d88093))

### Chores

- **git**: Remove CHANGELOG tracking
  ([`3466b68`](https://github.com/KitwareMedical/trame-slicer/commit/3466b68100c6b20fbafbab7338ab70d26e10617d))


## v0.2.0 (2025-04-16)

### Features

- **io_manager**: Add scene save to MRB / MRML
  ([`1a1a2b3`](https://github.com/KitwareMedical/trame-slicer/commit/1a1a2b3cc39252189cd367278b1c3025beba652b))


## v0.1.0 (2025-04-14)

### Features

- **api**: Change paths to use slicer package
  ([`e2639ad`](https://github.com/KitwareMedical/trame-slicer/commit/e2639ad6736203af0a6b6545c78ddca3b8c641ca))

- **segmentation**: (WIP) Add segment editor
  ([`8702402`](https://github.com/KitwareMedical/trame-slicer/commit/870240271255ca84020d0399653f188340361955))

- **segmentation**: Refactoring
  ([`3deb00c`](https://github.com/KitwareMedical/trame-slicer/commit/3deb00c6886b666c51bd22b301f3a02bc02341ad))

- **segmentation**: Scissor effect in slice views
  ([`5b55f3b`](https://github.com/KitwareMedical/trame-slicer/commit/5b55f3be491c7be9702c389b6165112de3d46419))


## v0.0.2 (2025-04-08)

### Bug Fixes

- **packaging**: Add missing manifest file
  ([`51bc005`](https://github.com/KitwareMedical/trame-slicer/commit/51bc0059da861458c0e968b3d37979021f06614f))

- **view**: Fix resize hang on linux
  ([`27c2a93`](https://github.com/KitwareMedical/trame-slicer/commit/27c2a93736ba01d84590842f0a5ea8b58f95d1c7))

- **view**: Rollback monitored resize event
  ([`f2de24e`](https://github.com/KitwareMedical/trame-slicer/commit/f2de24e316ab137dd52735204788e4bb50542e6a))

### Documentation

- Add missing acknowledgments
  ([`032f400`](https://github.com/KitwareMedical/trame-slicer/commit/032f400c0004369eddb55b19a5174d3b997d3e96))

### Features

- V0.0.2
  ([`e0128d6`](https://github.com/KitwareMedical/trame-slicer/commit/e0128d6eebde256bd4c510be1f4d8b1170431ff0))

- **layout**: Add argument to specify layout size
  ([`4f3c0a4`](https://github.com/KitwareMedical/trame-slicer/commit/4f3c0a4f499f8e58ea3168ad1ce5afe7fb0c329d))

- **rca_view**: Bump RCA version
  ([`3626778`](https://github.com/KitwareMedical/trame-slicer/commit/3626778b06a9d09fe372218239ca92c80105631a))

- **view**: Update interactor resize event
  ([`05e7267`](https://github.com/KitwareMedical/trame-slicer/commit/05e7267a2eea3a953fa5fdc45b401401e898f4e2))

- **view_layout**: Add quick access to 3d view properties
  ([`b1fefcd`](https://github.com/KitwareMedical/trame-slicer/commit/b1fefcdad50c05506b670451a695b66b9856a77a))

- **views**: Add zoom in / out
  ([`99cf3e9`](https://github.com/KitwareMedical/trame-slicer/commit/99cf3e94724bedee7d8c229620910b038806a2ee))


## v0.0.1 (2025-01-30)

- Initial Release
