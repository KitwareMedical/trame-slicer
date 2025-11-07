# Segmentation editor

## Interaction diagram




## Responsibility

Responsible for handling the following objects :

- Segmentation effects: the list of effects which can be activated and modify the segmentation depending on user or
  scripted interaction.
    - Each segmentation editor instance handles their own segmentation effect
    - The list of builtin effects is accessible as class attribute
    - The list of builtin effects can be injected into the segmentation editor
- Active segmentation: The object containing both informations of source volume and segmentation node containing the
  segmentation of its associated volume.
    - The current segmentation object
- Segmentation modifier: The object responsible for modifying the active segmentation and used by the different
  segmentation effects.
- UndoStack (optional): The Undo / Redo command stack modified when the segmentation is applied.

## Principles

The segmentation editor is responsible for handling the segmentation logic of the application.
It provides simplified API to activate or deactivate a current segmentation and modify it.

At creation, it will create its segment editor node holding its parameters. The segment editor node should not be
modified externally and is created as a node singleton linked to the segmentation editor.

Once initialized, the editor can be used to manage a segmentation using its `set_active_segmentation` method.

Segmentation effects can be activated using the `set_active_effect_type` method.
If the effect type is not yet registered, it will be automatically registered then.
 

