"""Two things can be silently wrong here: the address arithmetic and the word
order. Both produce a plausible number when they are wrong, so both are tested.
-- no hardware needed.

    python3 -m pytest tests -q
"""

import importlib.util
import os

import pytest

# The module filename has a dash in it, so a plain import will not work.
_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "exporter-ecoadapt",
                     "reader-ecoadapt.py")
_spec = importlib.util.spec_from_file_location("exporter_ecoadapt", _PATH)
exporter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exporter)


@pytest.mark.parametrize("connector,channel,expected", [
    # Integration manual annex 5.1, active energy import index (start 28, wpc 2).
    (1, 1, 28), (1, 2, 30), (2, 1, 34), (6, 3, 62),
])
def test_get_addr_matches_manual_annex_5_1(connector, channel, expected):
    assert exporter.get_addr(28, connector, channel, wpc=2) == expected


def test_get_addr_covers_each_block_exactly():
    """Last channel + its second word must equal the manual's end address."""
    assert exporter.get_addr(352, 1, 1, wpc=2) == 352
    assert exporter.get_addr(352, 6, 3, wpc=2) + 1 == 387      # voltage  352..387
    assert exporter.get_addr(424, 6, 3, wpc=2) + 1 == 459      # frequency 424..459
    assert exporter.get_addr(8, 6, 3, wpc=1) == 25             # config      8..25


def test_voltage_decodes_to_mains():
    """Registers 352-353 of the captured dump."""
    assert exporter.decode_float32(49709, 17262) == pytest.approx(238.76, abs=0.01)


def test_word_order_matters():
    """Swapped words give -43.32: wrong, but plausible enough to ship unnoticed."""
    assert exporter.decode_float32(17262, 49709) == pytest.approx(-43.32, abs=0.01)