from fractions import Fraction
import numpy as np

def determinant(matrix):
    size = len(matrix)


        # Base case: 2x2 matrix
    if size == 1:
        return matrix[0][0]
    elif size == 2:
        return matrix[0, 0] * matrix[1, 1] - matrix[0, 1] * matrix[1, 0]

    det = Fraction(0, 1)
    for j in range(size):
        det += matrix[0, j] * cofactor(matrix, 0, j)

    return det


def cofactor(matrix, row, col):
    minor = np.delete(np.delete(matrix, row, axis=0), col, axis=1)
    sign = (-1) ** (row + col)
    return sign * determinant(minor)


def transpose(matrix):
    return matrix.transpose()


def inverse(matrix):
    """
    Calcula la inversa de una matriz usando el método de la matriz adjunta
    """
    # Convertir la matriz a numpy array si no lo es ya
    matrix = np.array(matrix)
    rows, cols = matrix.shape
    
    if rows != cols:
        raise ValueError("La matriz debe ser cuadrada")
    
    # Calcular el determinante
    det = determinant(matrix)
    if det == 0:
        raise ValueError("La matriz es singular (determinante = 0)")
    
    # Calcular la matriz adjunta
    adjugate = np.zeros((rows, cols))
    for i in range(rows):
        for j in range(cols):
            # Calcular el cofactor
            minor = np.delete(np.delete(matrix, i, 0), j, 1)
            cofactor = determinant(minor) * (-1) ** (i + j)
            adjugate[j, i] = cofactor  # Transponer al mismo tiempo
    
    # Convertir elementos de la adjunta y determinante a Fraction
    adj_frac = array_to_fraction(adjugate)
    det_frac = Fraction(det).limit_denominator()
    
    # Calcular la inversa dividiendo cada elemento de la adjunta por el determinante
    inv_matrix = np.array([[adj_frac[i, j] / det_frac for j in range(cols)] for i in range(rows)])
    
    return inv_matrix

def array_to_fraction(arr):
    """
    Convierte un array numpy a fracciones
    """
    to_fraction = lambda t: Fraction(float(t)).limit_denominator()
    vfunc = np.vectorize(to_fraction)
    return vfunc(arr)


if __name__ == "__main__":

    # Example usage:
    A = np.array([
        [Fraction(2, 1), Fraction(0, 1), Fraction(2, 1), Fraction(2,1)],
        [Fraction(0, 1), Fraction(2, 1), Fraction(4, 1), Fraction(0,1)],
        [Fraction(0, 1), Fraction(0, 1), Fraction(6, 1), Fraction(5,1)],
        [Fraction(1, 1), Fraction(1, 1), Fraction(2, 1), Fraction(5,1)]
    ])

    # A = np.array ([[Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)],
    #  [Fraction(0, 1), Fraction(1, 1), Fraction(0, 1)],
    #  [Fraction(0, 1), Fraction(0, 1), Fraction(1, 1)]])


    determinant(A)

    A_inv = inverse(A)

    # Display the result
    for row in A_inv:
        print(row)

    print("fnished")