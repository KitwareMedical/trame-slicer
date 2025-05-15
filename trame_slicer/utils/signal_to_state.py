from __future__ import annotations

from trame_server.state import State
from trame_server.utils.asynchronous import create_task
from undo_stack import Signal, SignalContainer


def connect_signal_emit_values_to_state(signal: Signal, state: State, *, default=None, prefix=""):
    name = prefix + signal.name

    def inner(*args, **_):
        if len(args) == 1:
            args = args[0]

        async def set_state():
            state[name] = args
            state.flush()

        create_task(set_state())

    signal.connect(inner)
    if default:
        state[name] = default


def connect_all_signals_emitting_values_to_state(signal_container: SignalContainer, state: State):
    for signal in signal_container.signals():
        if len(signal.type_info) > 0:
            connect_signal_emit_values_to_state(signal, state)
