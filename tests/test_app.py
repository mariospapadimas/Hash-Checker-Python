"""Controller lifecycle keeps old workers away from destroyed widgets."""

from types import SimpleNamespace

import pytest

from src import app
from tests.helpers import FakeParent, FakeWidget


@pytest.mark.parametrize("selection", ["Verify Files Mode", "Compare Hashes Mode"])
def test_switch_disposes_before_destroying_widgets(monkeypatch, selection):
    """Teardown ordering is observable before a replacement mode is drawn."""
    events = []
    controller = object.__new__(app.HashChecker)
    controller.content_frame = FakeParent()
    controller.mode_select = FakeWidget(text=selection)
    controller.design = object()
    controller.active_mode = SimpleNamespace(dispose=lambda: events.append("dispose"))
    controller.content_frame.children.append(
        SimpleNamespace(destroy=lambda: events.append("destroy"))
    )

    class ReplacementMode:
        # pylint: disable=too-few-public-methods
        """Track mode construction and drawing, without a display."""

        def __init__(self, _parent, _design):
            events.append("construct")

        def draw_ui(self):
            """Drawing must occur only after the previous mode is disposed."""
            events.append("draw")

    monkeypatch.setattr(app, "VerifyFilesMode", ReplacementMode)
    monkeypatch.setattr(app, "CompareHashesMode", ReplacementMode)
    controller.on_selection_change()
    assert events == ["dispose", "destroy", "construct", "draw"]
    assert isinstance(controller.active_mode, ReplacementMode)


def test_closing_disposes_active_mode():
    """Closing the application also stops polling before root destruction."""
    events = []
    controller = object.__new__(app.HashChecker)
    controller.active_mode = SimpleNamespace(dispose=lambda: events.append("dispose"))
    controller.root = SimpleNamespace(destroy=lambda: events.append("destroy"))
    controller.close()
    assert events == ["dispose", "destroy"]
