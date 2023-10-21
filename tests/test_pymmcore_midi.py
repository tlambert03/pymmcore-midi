from unittest.mock import MagicMock

import mido
import pytest

from pymmcore_midi import XTouchMini


@pytest.fixture
def mock_xtouch(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_in = MagicMock()
    mock_out = MagicMock()

    def _mock_open_input(device_name: str) -> mido.ports.BaseInput:
        if device_name == "X-TOUCH MINI":
            return mock_in

    def _mock_open_output(device_name: str) -> mido.ports.BaseOutput:
        if device_name == "X-TOUCH MINI":
            return mock_out

    monkeypatch.setattr(mido, "open_input", _mock_open_input)
    monkeypatch.setattr(mido, "open_output", _mock_open_output)

    yield mock_in, mock_out


def test_x_touch_output(mock_xtouch) -> None:
    _, mock_out = mock_xtouch
    mini = XTouchMini()
    assert len(mini.knob) == 18
    assert len(mini.button) == 48
    assert repr(mini.knob)
    assert 1 in mini.knob

    buttons = {
        "rewind": 18,
        "fast_forward": 19,
        "loop": 20,
        "stop": 21,
        "play": 22,
        "record": 23,
    }
    for name, note in buttons.items():
        btn = getattr(mini, name)
        btn.press()
        msg = mido.Message("note_on", channel=10, note=note, velocity=64, time=0)
        mock_out.send.assert_called_once_with(msg)
        mock_out.reset_mock()
        btn.release()
        msg = mido.Message("note_off", channel=10, note=note, velocity=64, time=0)
        mock_out.send.assert_called_once_with(msg)
        mock_out.reset_mock()

    knob4 = mini.knob[4]
    knob4.set_value(20)
    msg = mido.Message("control_change", channel=10, control=4, value=20, time=0)
    mock_out.send.assert_called_once_with(msg)

    mini.close()


def test_x_touch_intput(mock_xtouch) -> None:
    mock_in, _ = mock_xtouch
    mini = XTouchMini()
    knob4 = mini.knob[4]

    mock = MagicMock()
    knob4.changed.connect(mock)
    msg = mido.Message("control_change", channel=10, control=4, value=30, time=0)
    mock_in.callback(msg)
    mock.assert_called_once_with(30)
    mock.reset_mock()

    btn3 = mini.button[3]
    btn3.pressed.connect(mock)
    msg = mido.Message("note_on", channel=10, note=3, velocity=64, time=0)
    mock_in.callback(msg)
    mock.assert_called_once()
    mock.reset_mock()

    btn3.released.connect(mock)
    msg = mido.Message("note_off", channel=10, note=3, velocity=64, time=0)
    mock_in.callback(msg)
    mock.assert_called_once()

    mini.close()
