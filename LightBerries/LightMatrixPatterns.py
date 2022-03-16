from typing import Any, Tuple
from nptyping import NDArray
import numpy as np
from LightBerries.LightPixels import DEFAULT_PIXEL_ORDER
from enum import IntEnum


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


if __name__ == "__main__":
    x = Spectrum(2, 4)
    # print(x)
