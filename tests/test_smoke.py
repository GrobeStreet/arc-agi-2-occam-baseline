import numpy as np

import dsl


def test_dsl_import_and_rot90_is_deterministic():
    grid = np.array([[1, 2], [3, 4]])
    expected = np.array([[2, 4], [1, 3]])

    actual = dsl.GEOM["rot90"](grid)

    np.testing.assert_array_equal(actual, expected)
    assert dsl._bg(np.array([[0, 0], [0, 7]])) == 0
