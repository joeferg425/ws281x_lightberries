from __future__ import annotations
import numpy as np
import numpy.typing

o = 0
l = 1  # noqa : dont care


def _init_letter(arry):
    from lightberries.matrix_patterns import DEFAULT_MATRIX_ORDER, MatrixOrder

    if DEFAULT_MATRIX_ORDER == MatrixOrder.TraverseColumnThenRow:
        arry = arry.T

    return np.dstack([arry, arry, arry])


class letters:
    A = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, l, o, o, o, o, o, o, o],
                [o, o, o, o, o, l, o, l, o, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, l, o, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, l, o, o, o, o],
                [o, o, o, l, l, l, l, l, l, l, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, l, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    B = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, o, o, o, o, o],
                [o, l, o, o, o, l, o, o, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, l, l, l, l, o, o, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, l, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    C = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, l, o, o, o],
                [o, o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, l, o, o],
                [o, o, o, l, l, l, l, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    D = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, o, o, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o, o],
                [o, l, l, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    E = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, l, l, l, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    F = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, l, l, l, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    G = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, l, l, l, o, o],
                [o, l, o, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    H = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, l, l, l, l, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    I = _init_letter(  # noqa : dont care
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, l, l, l, l, l, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    J = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, l, o, o, l, o, o, o, o, o],
                [o, l, o, o, l, o, o, o, o, o],
                [o, l, o, o, l, o, o, o, o, o],
                [o, o, l, l, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    K = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, l, o, o, l, o, o, o, o],
                [o, l, o, l, o, o, o, o, o],
                [o, l, l, l, o, o, o, o, o],
                [o, l, o, o, l, o, o, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    L = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    M = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, l, o, o, o, l, l, o, o],
                [o, l, l, o, o, o, l, l, o, o],
                [o, l, o, l, o, l, o, l, o, o],
                [o, l, o, l, o, l, o, l, o, o],
                [o, l, o, o, l, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    N = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, l, o, o, o, o, l, o, o],
                [o, l, l, o, o, o, o, l, o, o],
                [o, l, o, l, o, o, o, l, o, o],
                [o, l, o, l, o, o, o, l, o, o],
                [o, l, o, o, l, o, o, l, o, o],
                [o, l, o, o, l, o, o, l, o, o],
                [o, l, o, o, o, l, o, l, o, o],
                [o, l, o, o, o, l, o, l, o, o],
                [o, l, o, o, o, o, l, l, o, o],
                [o, l, o, o, o, o, l, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    O = _init_letter(  # noqa : dont care
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    P = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, l, l, l, l, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    Q = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, l, o, o, l, o, o],
                [o, l, o, o, o, l, o, l, o, o],
                [o, l, o, o, o, o, l, l, o, o],
                [o, o, l, o, o, o, l, l, o, o],
                [o, o, o, l, l, l, o, o, l, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    R = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, l, l, l, l, o, o, o],
                [o, l, o, o, l, o, o, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    S = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, o, l, l, l, l, o, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o],
                [o, o, o, l, l, l, o, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, l, o, o],
                [o, o, l, l, l, l, o, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    T = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    U = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    V = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    W = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, o, o, o, o, l, o, o, o],
                [o, o, o, l, o, o, o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, l, o, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, l, o, l, o, o, o, o],
                [o, o, o, o, l, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    X = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    Y = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, l, o, l, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    Z = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, l, o, o, o, o],
                [o, o, o, o, o, l, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    SPACE = _init_letter(
        np.array(
            [
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
                [o, o, o, o, o],
            ]
        )
    )
    APOSTROPHE = _init_letter(
        np.array(
            [
                [o, o, o],
                [o, o, o],
                [o, l, o],
                [l, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
            ]
        )
    )
    COMMA = _init_letter(
        np.array(
            [
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, o, o],
                [o, l, o],
                [o, l, o],
                [l, o, o],
            ]
        )
    )
    EXCLAMATION = _init_letter(
        np.array(
            [
                [o, o, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, o, o, o],
                [o, o, o, o],
                [o, l, o, o],
                [o, l, o, o],
                [o, o, o, o],
            ]
        )
    )
    ZERO = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, l, l, o, o],
                [o, l, o, o, o, o, l, l, o, o],
                [o, l, o, o, o, l, o, l, o, o],
                [o, l, o, o, o, l, o, l, o, o],
                [o, l, o, o, l, o, o, l, o, o],
                [o, l, o, o, l, o, o, l, o, o],
                [o, l, o, l, o, o, o, l, o, o],
                [o, l, o, l, o, o, o, l, o, o],
                [o, l, l, o, o, o, o, l, o, o],
                [o, l, l, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    ONE = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, l, l, o, o, o, o],
                [o, l, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o],
                [o, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o],
            ]
        )
    )
    TWO = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, o, l, l, l, o, o, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, l, o, o, o, o],
                [o, o, o, l, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, o, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    THREE = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, o, l, l, l, o, o, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, l, l, l, o, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    FOUR = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, l, l, o, o, o],
                [o, o, o, o, l, l, o, o, o],
                [o, o, o, l, o, l, o, o, o],
                [o, o, o, l, o, l, o, o, o],
                [o, o, l, o, o, l, o, o, o],
                [o, o, l, o, o, l, o, o, o],
                [o, l, o, o, o, l, o, o, o],
                [o, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    FIVE = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, l, l, l, o, o, o, o],
                [o, l, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    SIX = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, l, l, l, o, o, o],
                [o, o, o, l, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, o, o, o, o, o, o, o],
                [o, l, o, l, l, l, o, o, o, o],
                [o, l, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    SEVEN = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, o, l, o, o, o],
                [o, o, o, o, o, l, o, o, o, o],
                [o, o, o, o, o, l, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, o, l, o, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, o],
                [o, o, o, l, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o],
                [o, o, l, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    EIGHT = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    NINE = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, l, l, l, o, o, o, o],
                [o, o, l, o, o, o, l, o, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, l, o, o, o, o, o, l, o, o],
                [o, o, l, o, o, o, l, l, o, o],
                [o, o, o, l, l, l, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )
    EQUALS = _init_letter(
        np.array(
            [
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, l, l, l, l, l, l, l, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
                [o, o, o, o, o, o, o, o, o, o],
            ]
        )
    )


def letters_to_matrices(text: str) -> list[numpy.typing.NDArray]:
    retval = []
    for letr in text.upper():
        if letr in dir(letters):
            retval.append(getattr(letters, letr))
        elif letr == " ":
            retval.append(getattr(letters, "SPACE"))
        elif letr == "'":
            retval.append(getattr(letters, "APOSTROPHE"))
        elif letr == ",":
            retval.append(getattr(letters, "COMMA"))
        elif letr == "!":
            retval.append(getattr(letters, "EXCLAMATION"))
        elif letr == "0":
            retval.append(getattr(letters, "ZERO"))
        elif letr == "1":
            retval.append(getattr(letters, "ONE"))
        elif letr == "2":
            retval.append(getattr(letters, "TWO"))
        elif letr == "3":
            retval.append(getattr(letters, "THREE"))
        elif letr == "4":
            retval.append(getattr(letters, "FOUR"))
        elif letr == "5":
            retval.append(getattr(letters, "FIVE"))
        elif letr == "6":
            retval.append(getattr(letters, "SIX"))
        elif letr == "7":
            retval.append(getattr(letters, "SEVEN"))
        elif letr == "8":
            retval.append(getattr(letters, "EIGHT"))
        elif letr == "9":
            retval.append(getattr(letters, "NINE"))
        elif letr == "=":
            retval.append(getattr(letters, "EQUALS"))
    return retval
