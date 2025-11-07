# Segmentation editor

The following documentation lists the responsibility, features and design
principles of the Segmentation Editor. Note that, contrary to its 3D Slicer's
counterpart, the trame-slicer Segmentation Editor is purely a logic class and
doesn't provide any user interface.

Its API was designed to simplify integration into any UI and any workflow.

## Difference with 3D Slicer

trame-slicer segmentation editor is not based on 3D Slicer's segmentation editor
as 3D Slicer's segmentation editor heavily relies on Qt for its inner workings.

Core functionalities can be refactored and adapted to work in both environments
and some efforts have already been made in this direction.

## Diagrams

### Main classes

The diagram below presents the main classes interacting with the segmentation
editor. Some interactions are left out to avoid cluttering the diagram.

```{eval-rst}
.. mermaid:: editor_class_relationship.mmd
   :caption: Segmentation Editor Class interaction
   :align: center
```

The Segmentation Editor is responsible for handling the following objects :

- Segmentation effects: the list of effects which can be activated and modify
  the segmentation depending on user or scripted interaction.
  - Each segmentation editor instance handles their own segmentation effect
  - The list of builtin effects is accessible as class attribute
  - The list of builtin effects can be injected into the segmentation editor
- Active segmentation: The object containing both information of source volume
  and segmentation node containing the segmentation of its associated volume.
  - The current segmentation object
- Segmentation modifier: The object responsible for modifying the active
  segmentation and used by the different segmentation effects.
- UndoStack (optional): The Undo / Redo command stack modified when the
  segmentation is applied.

## Design principle

The segmentation editor is responsible for handling the segmentation logic of
the application. It provides a simplified API to activate or deactivate a
current segmentation and modify it.

At creation, it will create its segment editor node holding its parameters. The
segment editor node should not be modified externally and is created as a node
singleton linked to the segmentation editor. Each instance of the segmentation
editor will have its own segmentation editor node.

Once initialized, the editor should be used to manage the active segmentation by
using its `set_active_segmentation` method. Setting the active segmentation will
create a new instance of the SegmentModifier class and this instance will be
used by the active effects to modify the segmentation of the current volume node
/ segmentation node.

Segmentation effects can be activated using the `set_active_effect_type` method.
If the effect type is not yet registered, it will be automatically registered
then.

Each segmentation effect can have one or more effect pipelines. The effect
pipelines are the rendered effect visible in the Slice and Threed views such as
paint / erase brush effects.

Effects logic, such as apply, preview, auto threshold, etc., should be called
directly from the effect instance.

The following example shows an example of wiring the threshold effect with
trame:
