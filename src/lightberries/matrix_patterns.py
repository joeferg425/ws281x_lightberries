from __future__ import annotations
import logging
from typing import Any
import numpy as np
from lightberries.exceptions import LightBerryException, PatternException
from lightberries.pixel import Pixel
from lightberries.array_patterns import ArrayPattern
from enum import IntEnum

LOGGER = logging.getLogger("lightBerries")


class MatrixOrder(IntEnum):
    TraverseRowThenColumn = 0
    TraverseColumnThenRow = 1


DEFAULT_MATRIX_ORDER = MatrixOrder.TraverseColumnThenRow


def SingleLED(xRange: int, yRange: int) -> np.ndarray[(Any, Any, 3), np.int32]:
    matrix = np.zeros((yRange, xRange, 3))
    matrix[0, 0, :] = 255
    return matrix


def Spectrum(xRange: int, yRange: int) -> np.ndarray[(Any, Any, 3), np.int32]:
    matrix = np.zeros((yRange, xRange, 3))
    row_scalers = np.linspace(0, 127.5, xRange)
    column_scalers = np.linspace(0, 127.5, yRange)
    matrix[:, :, 0] += column_scalers
    matrix[:, :, 0] = np.transpose(matrix.transpose((1, 0, 2))[:, :, 0] + row_scalers)
    matrix[:, :, 1] += np.flip(column_scalers)
    matrix[:, :, 1] = np.transpose(matrix.transpose((1, 0, 2))[:, :, 1] + np.flip(row_scalers))
    matrix[:, :, 2] += np.flip(column_scalers)
    matrix[:, :, 2] = np.transpose(matrix.transpose((1, 0, 2))[:, :, 2] + row_scalers)
    return matrix  # .reshape((3,xRange * yRange))


def Spectrum2(xRange: int, yRange: int) -> np.ndarray[(Any, Any, 3), np.int32]:
    matrix = np.zeros((yRange, xRange, 3))
    matrix[:, :, 0] += (np.cos(np.linspace(0, 2 * np.pi, yRange)) * 127.5) + 127.5
    matrix[:, :, 1] += (np.cos(np.linspace(0, 4 * np.pi, yRange)) * 127.5) + 127.5
    matrix[:, :, 2] += (np.cos(np.linspace(0, 6 * np.pi, yRange)) * 127.5) + 127.5
    for i in range(3):
        for j in range(xRange):
            matrix[j, :, i] = np.roll(matrix[j, :, i], j + (i * int(xRange / 3)))
    return matrix


def SolidColorMatrix(
    xRange: int, yRange: int, color: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_COLOR_SEQUENCE[0]
) -> np.ndarray[(3, Any), np.int32]:
    """Creates matrix of RGB tuples that are all one color.

    Args:
        xRange: the total desired rows in matrix
        yRange: the total desired rows in matrix
        color: a pixel object defining the rgb values you want in the pattern

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        if isinstance(color, np.ndarray):
            _color = Pixel(color)
        else:
            _color = color
        matrix = np.ones((yRange, xRange, 3))
        matrix[:, :, 0] *= _color.array[0]
        matrix[:, :, 1] *= _color.array[1]
        matrix[:, :, 2] *= _color.array[2]
        return matrix
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise PatternException from ex


def TextMatrix(text: str, color: np.ndarray[(Any, 3), np.int32]) -> np.ndarray[(Any, Any, 3), np.int32]:
    from lightberries.matrix_letters import letters_to_matrices

    letters = letters_to_matrices(text + "     ")
    total_length = 0
    matrix = np.ndarray
    if DEFAULT_MATRIX_ORDER == MatrixOrder.TraverseColumnThenRow:
        total_length = sum([matrix.shape[0] for matrix in letters])
        matrix = np.zeros((total_length, letters[0].shape[1], 3))
        idx = 0
        for letter in letters:
            matrix[idx : idx + letter.shape[0], : letter.shape[1], :] = letter
            idx += letter.shape[0]
    elif DEFAULT_MATRIX_ORDER == MatrixOrder.TraverseRowThenColumn:
        total_length = sum([matrix.shape[1] for matrix in letters])
        matrix = np.zeros((letters[0].shape[0], total_length, 3))
        idx = 0
        for letter in letters:
            matrix[: letter.shape[0], idx : idx + letter.shape[1], :] = letter
            idx += letter.shape[1]
    return matrix * color
