# CHANGELOG


## v0.2.0 (2025-04-16)

### Features

- **io_manager**: Add scene save to MRB / MRML
  ([`1a1a2b3`](https://github.com/KitwareMedical/trame-slicer/commit/1a1a2b3cc39252189cd367278b1c3025beba652b))


## v0.1.0 (2025-04-14)

### Features

- **api**: Change paths to use slicer package
  ([`e2639ad`](https://github.com/KitwareMedical/trame-slicer/commit/e2639ad6736203af0a6b6545c78ddca3b8c641ca))

* Change paths to use slicer package for Slicer app compatibility

- **segmentation**: (wip) Add segment editor
  ([`8702402`](https://github.com/KitwareMedical/trame-slicer/commit/870240271255ca84020d0399653f188340361955))

* Add segmentation editor and paint/erase effect * Add segmentation editor scissor effect * Add
  examples

- **segmentation**: Refactoring
  ([`3deb00c`](https://github.com/KitwareMedical/trame-slicer/commit/3deb00c6886b666c51bd22b301f3a02bc02341ad))

* Rename SegmentationEffect to Widget * Rename SegmentationTool to Effect * Rename
  SegmentationManager to SegmentationEditor * Rename SegmentationEditor to SegmentModifier * Move
  Segmentation logic to SegmentationEditor * Fix segmentation sanitize when using empty segment *
  Fix segmentation export to NIFTI file * Move IO to segmentation editor * Fix brush scaling in
  absolute mode and default to invariant * Fix events sent twice in Slice views * Move events
  handling in views in dedicated classes * Add SegmentRegionMask responsible for region masking *
  Fix failing tests * Add support for segmentation Undo / Redo * Add helper for signal / slot
  connection * Add segmentation button to medical example * Fix brush diameter update when switching
  views * Add Undo / Redo functionnalities * Update example * Migrate to pyproject.toml * Bump
  pre-commit rules * Fix pre-commit errors

- **segmentation**: Scissor effect in slice views
  ([`5b55f3b`](https://github.com/KitwareMedical/trame-slicer/commit/5b55f3be491c7be9702c389b6165112de3d46419))


## v0.0.2 (2025-04-08)

### Bug Fixes

- **packaging**: Add missing manifest file
  ([`51bc005`](https://github.com/KitwareMedical/trame-slicer/commit/51bc0059da861458c0e968b3d37979021f06614f))

* Add missing manifest file to install the trame-slicer resources

- **view**: Fix resize hang on linux
  ([`27c2a93`](https://github.com/KitwareMedical/trame-slicer/commit/27c2a93736ba01d84590842f0a5ea8b58f95d1c7))

https://github.com/Kitware/trame-rca/pull/18

- **view**: Rollback monitored resize event
  ([`f2de24e`](https://github.com/KitwareMedical/trame-slicer/commit/f2de24e316ab137dd52735204788e4bb50542e6a))

* Rollback 05e7267a2eea3a953fa5fdc45b401401e898f4e2 which doesn't work for Linux systems.

### Documentation

- Add missing acknowledgments
  ([`032f400`](https://github.com/KitwareMedical/trame-slicer/commit/032f400c0004369eddb55b19a5174d3b997d3e96))

* Add missing HINT & COSY acknowledgments

### Features

- V0.0.2
  ([`e0128d6`](https://github.com/KitwareMedical/trame-slicer/commit/e0128d6eebde256bd4c510be1f4d8b1170431ff0))

- **layout**: Add argument to specify layout size
  ([`4f3c0a4`](https://github.com/KitwareMedical/trame-slicer/commit/4f3c0a4f499f8e58ea3168ad1ce5afe7fb0c329d))

- **rca_view**: Bump RCA version
  ([`3626778`](https://github.com/KitwareMedical/trame-slicer/commit/3626778b06a9d09fe372218239ca92c80105631a))

* Bump RCA version and change default encoder to Turbo JPEG

- **view**: Update interactor resize event
  ([`05e7267`](https://github.com/KitwareMedical/trame-slicer/commit/05e7267a2eea3a953fa5fdc45b401401e898f4e2))

* Interactor WindowResizeEvent is scheduled to be deprecated / removed. Update to use ConfigureEvent
  instead.

- **view_layout**: Add quick access to 3d view properties
  ([`b1fefcd`](https://github.com/KitwareMedical/trame-slicer/commit/b1fefcdad50c05506b670451a695b66b9856a77a))

- **views**: Add zoom in / out
  ([`99cf3e9`](https://github.com/KitwareMedical/trame-slicer/commit/99cf3e94724bedee7d8c229620910b038806a2ee))

* Add helper methods to zoom in and out for Slice and 3D views


## v0.0.1 (2025-01-30)

### Bug Fixes

- **test**: Fix factory tests
  ([`159101c`](https://github.com/KitwareMedical/trame-slicer/commit/159101c330c43de9eafdc1cec01dd0c12b98ee82))

- **test**: Fix failing tests with VTK 9.4
  ([`78916bb`](https://github.com/KitwareMedical/trame-slicer/commit/78916bb596651a4a772f5fe8fa0e9dd5c4e8ee9c))

- **test**: Fix missing test dependency
  ([`b690082`](https://github.com/KitwareMedical/trame-slicer/commit/b6900827f1e9aa06959f619c085c85b3acd9ce9b))

- **views**: Fix 2D view resize
  ([`ffb1131`](https://github.com/KitwareMedical/trame-slicer/commit/ffb1131f025cc625a02a9d56fda5a22be6713793))

- **views**: Fix rendering for 2D Slices
  ([`95ac535`](https://github.com/KitwareMedical/trame-slicer/commit/95ac5350c92947a4b95acc6f367956efbf3a31df))

### Chores

- Mark test data folder as LFS
  ([`f21db41`](https://github.com/KitwareMedical/trame-slicer/commit/f21db41db36f8d6232e47ddaf48158f67c54bc34))

- Remove outdated rendering pool
  ([`356e942`](https://github.com/KitwareMedical/trame-slicer/commit/356e942448498cc5c397f54e5095004eb994dfca))

- Remove test data from repository
  ([`6f7e145`](https://github.com/KitwareMedical/trame-slicer/commit/6f7e145d70474bbd78129b2c742f795678496ddb))

### Documentation

- Update library documentation
  ([`f2a5234`](https://github.com/KitwareMedical/trame-slicer/commit/f2a52345eabecf78048b6f7051eb4e46c1fff022))

- Update readme and contributing
  ([`7ec1c6a`](https://github.com/KitwareMedical/trame-slicer/commit/7ec1c6a505fc24256a5a4c61b6f828aab045db36))

### Features

- **api**: Change imports for Slicer application compatibility
  ([`6f43b9e`](https://github.com/KitwareMedical/trame-slicer/commit/6f43b9e2dd2b40661a0e79133926d64f4bb59dea))

- **api**: Change view API to use factories for displayable manager creation
  ([`4c9f6a4`](https://github.com/KitwareMedical/trame-slicer/commit/4c9f6a42fafeec6dce2abcd1a4265828fd831d0e))

- **api**: Improve trame Slicer folder structure
  ([`2c33ed2`](https://github.com/KitwareMedical/trame-slicer/commit/2c33ed2d76d7957a018c1cc4d293a1e333050759))

- **api**: Move files to git project root
  ([`4864f5b`](https://github.com/KitwareMedical/trame-slicer/commit/4864f5bd4c3f5281ec2d361f6d3ecf4a3b32ff8e))

- **api**: Rename library to trame-slicer
  ([`e79f9a2`](https://github.com/KitwareMedical/trame-slicer/commit/e79f9a26e93be32377e87f6d4417f8ac24597610))

* Rename library to trame-slicer for future usage consistency * SlicerTrame is reserved for Slicer
  integrated trame-slicer extension

- **core**: Add custom share directory
  ([`9f26de6`](https://github.com/KitwareMedical/trame-slicer/commit/9f26de6a7b0db8048626b3d313e62d6150193455))

- **core**: Add file loading from front end
  ([`634708c`](https://github.com/KitwareMedical/trame-slicer/commit/634708c8af04bf4f442d1165190b06ec9eed06e9))

* Add file loading from front end * Automatically display the first volume * Fix Trame / Slicer
  synchronization for 2D sliders and 3D view reset * Add background color property to view
  definitions * Fix 2D view orientation to match volume orientation

- **core**: Add markups handling
  ([`d74153a`](https://github.com/KitwareMedical/trame-slicer/commit/d74153ac735437f51eaa7f62b881a1d9fa8dc810))

- **core**: Add slice 3D view visibility
  ([`5032996`](https://github.com/KitwareMedical/trame-slicer/commit/5032996e3c79838a5c6818d8bee46b4549cef866))

* Add Slice 3D view visibility * Add helper functions in io_manager * Move resources to dedicated
  folder * Initialize additional logic * Bump minimum required trame-rca version to supporting mouse
  hover

- **core**: Add volume rendering shift helpers
  ([`550953f`](https://github.com/KitwareMedical/trame-slicer/commit/550953f3aed077ee35e70cd6cfd2e6f47a298c46))

* Add VolumeProperty class responsible for VR shift logic * Add VolumeRendering vr shift logic * Add
  3D Slicer resources for preset icons

- **example**: Create demo content with simplistic UI
  ([`b96a875`](https://github.com/KitwareMedical/trame-slicer/commit/b96a875d7c2a43075ca92c4488c9964a4680d145))

- **example**: Split medical view example
  ([`cff98d3`](https://github.com/KitwareMedical/trame-slicer/commit/cff98d30d21dbc7b37a72e382696b907d6788bb5))

* Split medical viewer example code into modularized widgets * Add example for the VR Slider * Add
  smoke test for medical viewer example

- **io-manager**: Add explicit options to save / load models without coordinate change
  ([`cd57308`](https://github.com/KitwareMedical/trame-slicer/commit/cd57308ad714c365af703992779a4cd4dc7bce86))

- **segmentation**: Add segmentation
  ([`5226c1e`](https://github.com/KitwareMedical/trame-slicer/commit/5226c1edf226639c17cf8372c6d1b8bb3a9f47ac))

* Add segmentation handling in the POC

- **views**: Add additional support for RCA encoding formats
  ([`887a5d2`](https://github.com/KitwareMedical/trame-slicer/commit/887a5d2082a6f4d7b8c8fb41eab0763652cc2103))

- **views**: Add component responsible for the layout
  ([`ca92047`](https://github.com/KitwareMedical/trame-slicer/commit/ca92047e8be4d86f9fdb6dc2e3996e4e505c1278))

* Refactor code structure for more clarity * Apply precommit rules * Add LayoutGrid component for
  displaying the view layout * Add ViewManager responsible for instantiating the views * Removed
  outdated classes and code

- **views**: Add mouse hover support
  ([`99552f9`](https://github.com/KitwareMedical/trame-slicer/commit/99552f9a0eefc0be23cc29d2785c06ff213807fb))

* Add mouse hover support * Fix double mouse release bug

- **views**: Add Slice and 3D view interaction
  ([`43861be`](https://github.com/KitwareMedical/trame-slicer/commit/43861bedf7d24232ea2760dbaff1bad0b629b421))

* Bump VTK version to 9.3 for serialization support * Add 2D Slice interaction * Add 3D View
  interaction in Remote Controlled Area * Add trame-vtklocal as dependency for local rendering * Add
  trame-rca as dependency for remote rendering

- **views**: Add Slice offset interaction
  ([`acf6b8f`](https://github.com/KitwareMedical/trame-slicer/commit/acf6b8f78bcd8a606cccee0f392d89a9f719e15c))

- **views**: Add View factory and hook with Slicer / Trame
  ([`f99b427`](https://github.com/KitwareMedical/trame-slicer/commit/f99b427ae21276199a65e29bf3a6afd510345663))

- **views**: Add view orientation marker / rulers
  ([`93dacc1`](https://github.com/KitwareMedical/trame-slicer/commit/93dacc1c5b232031418c4dc43d7db08531a97a56))

* Add helper function to activate orientation marker and ruler

- **views**: Add Volume Rendering
  ([`0b79e02`](https://github.com/KitwareMedical/trame-slicer/commit/0b79e029b52605bc0096db1d162eeb5eb76a68d5))

- **views**: Add Volume Rendering and 2D interaction refresh
  ([`b6cea3c`](https://github.com/KitwareMedical/trame-slicer/commit/b6cea3cc1537c3dc396768d1ca68963eda2c9442))

* Add strategy responsible for scheduled rendering * Add volume rendering in POC application * Add
  default scheduled rendering to direct rendering in unit tests

- **views**: Add WebP RCA encoding
  ([`a90173b`](https://github.com/KitwareMedical/trame-slicer/commit/a90173b5cbcba2a8f7669d027d30a1c2e24050e9))

- **views**: Factorize trame-rca utils components
  ([`8a62d35`](https://github.com/KitwareMedical/trame-slicer/commit/8a62d35ef36c4e549972eef77c4b68ff1c2ceb00))

* Factorize RCA components to use trame-rca utils implementation

- **views**: First working version of layout display
  ([`de91828`](https://github.com/KitwareMedical/trame-slicer/commit/de91828aa2a91da41ad42155c298c833f53cdff7))

* Change expected layout dict to dict of layout * Add fit to view to abstract view * Add rotate view
  to 3D view * Add option to fit to content when showing volume

- **views**: Improve rendering reactivity
  ([`44dd219`](https://github.com/KitwareMedical/trame-slicer/commit/44dd219b55b0a212ccf61af22db7b7460a0a3672))

* Improve rendering reactivity by implementing encoding and push as subprocesses

- **views**: Improve view creation and connectivity
  ([`9a07d6b`](https://github.com/KitwareMedical/trame-slicer/commit/9a07d6b358c8a2725256415847977d130b633c72))

* Add DisplayManager responsible for showing nodes depending on views * Update SlicerApp * Update
  TrameApp to reflect changes * Add IOManager responsible for loading volumes / models and
  segmentations * Add tests for loading DCM volume * Move test data to dedicated folder

- **views**: Make RCA overlay configurable
  ([`578e7c1`](https://github.com/KitwareMedical/trame-slicer/commit/578e7c1bde0d64a93be6d1c54b66364be3beb3e5))

* Allow injecting UI creation for the RCA views * Remove custom CSS for the vertical sliders * Add
  helpers to configure Vuetify sliders and connect them to Slicer views
