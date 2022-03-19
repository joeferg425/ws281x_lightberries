import logging
from typing import Any
from nptyping import NDArray
import numpy as np
from LightBerries.LightBerryExceptions import LightPatternException
from LightBerries.LightPixels import Pixel
from LightBerries.LightArrayPatterns import DEFAULT_COLOR_SEQUENCE
from enum import IntEnum

LOGGER = logging.getLogger("LightBerries")


class MatrixOrder(IntEnum):
    TraverseRowThenColumn = 0
    TraverseColumnThenRow = 1


DEFAULT_MATRIX_ORDER = MatrixOrder.TraverseColumnThenRow


def SingleLED(rowCount: int, columnCount: int) -> NDArray[(Any, Any, 3), np.int32]:
    matrix = np.zeros((rowCount, columnCount, 3))
    matrix[0, 0, :] = 255
    return matrix


def Spectrum(rowCount: int, columnCount: int) -> NDArray[(Any, Any, 3), np.int32]:
    matrix = np.zeros((rowCount, columnCount, 3))
    row_scalers = np.linspace(0, 127.5, rowCount)
    column_scalers = np.linspace(0, 127.5, columnCount)
    matrix[:, :, 0] += column_scalers
    matrix[:, :, 0] = np.transpose(matrix.transpose((1, 0, 2))[:, :, 0] + row_scalers)
    matrix[:, :, 1] += np.flip(column_scalers)
    matrix[:, :, 1] = np.transpose(matrix.transpose((1, 0, 2))[:, :, 1] + np.flip(row_scalers))
    matrix[:, :, 2] += np.flip(column_scalers)
    matrix[:, :, 2] = np.transpose(matrix.transpose((1, 0, 2))[:, :, 2] + row_scalers)
    return matrix  # .reshape((3,rowCount * columnCount))


def Spectrum2(rowCount: int, columnCount: int) -> NDArray[(Any, Any, 3), np.int32]:
    matrix = np.zeros((rowCount, columnCount, 3))
    matrix[:, :, 0] += (np.cos(np.linspace(0, 2 * np.pi, columnCount)) * 127.5) + 127.5
    matrix[:, :, 1] += (np.cos(np.linspace(0, 4 * np.pi, columnCount)) * 127.5) + 127.5
    matrix[:, :, 2] += (np.cos(np.linspace(0, 6 * np.pi, columnCount)) * 127.5) + 127.5
    for i in range(3):
        for j in range(rowCount):
            matrix[j, :, i] = np.roll(matrix[j, :, i], j + (i * int(rowCount / 3)))
    return matrix


def SolidColorMatrix(
    rowCount: int,
    columnCount: int,
    color: NDArray[(3,), np.int32] = DEFAULT_COLOR_SEQUENCE[0].array,
) -> NDArray[(3, Any), np.int32]:
    """Creates matrix of RGB tuples that are all one color.

    Args:
        rowCount: the total desired rows in matrix
        columnCount: the total desired rows in matrix
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
        if DEFAULT_MATRIX_ORDER == MatrixOrder.TraverseRowThenColumn:
            matrix = np.ones((rowCount, columnCount, 3))
        elif DEFAULT_MATRIX_ORDER == MatrixOrder.TraverseColumnThenRow:
            matrix = np.ones((columnCount, rowCount, 3))
        matrix[:, :, 0] *= _color.array[0]
        matrix[:, :, 1] *= _color.array[1]
        matrix[:, :, 2] *= _color.array[2]
        return matrix
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, SolidColorMatrix.__name__, str(ex))
        raise LightPatternException from ex


def TextMatrix(text: str, color: NDArray[(Any, 3), np.int32]) -> NDArray[(Any, Any, 3), np.int32]:
    from LightBerries.LightMatrixLetters import letters_to_matrices

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
