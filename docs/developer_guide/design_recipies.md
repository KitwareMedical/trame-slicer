# Design recipies

## Widget implementation

trame-slicer widgets should be cleanly split between UI component and Logic component to simplify maintenance and allow
cross compatibility of the developed components between 3D Slicer and trame.

To simplify this cross-compatibility, the UI and logic should rely on : 
- dataclasses for parameter handling
- Signal for UI connection

In the trame-slicer environment the py-undo-stack library is used to provide qt like Signals.
These signals are compatible with any callable connection in the 3D Slicer desktop environment.

## Dependency injection

UI and Logic components should rely on injected dependencies including `MRML Scene` and modules.

