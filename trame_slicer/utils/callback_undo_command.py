from __future__ import annotations

from undo_stack import UndoCommand


class CallbackUndoCommand(UndoCommand):
    """
    Simple UndoCommand which delegates to undo / redo callbacks.
    """

    def __init__(self, undo_callback, redo_callback, text=""):
        super().__init__()
        self._undo_callback = undo_callback
        self._redo_callback = redo_callback
        self._text = text

    def undo(self):
        self._undo_callback()

    def redo(self):
        self._redo_callback()
