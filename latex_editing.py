import numpy as np
from fractions import Fraction
import six




def array_to_fraction(arr):
    to_fraction = lambda t: Fraction(t).limit_denominator()
    vfunc = np.vectorize(to_fraction)
    return vfunc(arr)


def arrays_to_fraction(list_arr):
    list_arr_frac = list()
    for arr in list_arr:
        list_arr_frac.append(array_to_fraction(arr))
    return list_arr_frac


def fraction_to_tex(frac, use_dolar=False, frac_command=True):
    """
    Convierte una fracción a formato LaTeX
    """
    # Convertir a Fraction si es un float o numpy.float64
    if isinstance(frac, (float, np.float64)):
        frac = Fraction(float(frac)).limit_denominator()
    
    # Si ya es una Fraction, continuar con el procesamiento normal
    result = ""
    if frac.denominator == 1 or frac.denominator == 0:
        result = "{:.0f}".format(frac.numerator)
    else:
        if frac_command:
            result = "\\frac{{{}}}{{{}}}".\
                format(frac.numerator, frac.denominator)
        else:
            result = "{}/{}".format(frac.numerator, frac.denominator)

    if use_dolar:
        result = "${}$".format(result)

    return result


def matrix_to_tex(m, brackets="round", frac_command=True):
    if m.shape == (1,1):
        return fraction_to_tex(m[0][0], frac_command=frac_command)
    if brackets == "round":
        str = "\\begin{pmatrix}\n"
    for r in range(m.shape[0]):
        for c in range(m.shape[1]):
            element = m[r, c]
            if isinstance(element, Fraction):
                str += "{}".format(fraction_to_tex(element, use_dolar=False, frac_command=frac_command))
            elif int(element) == element:
                str += "{:.0f}".format(element)
            else:
                str += "{}".format(element)
            if c != m.shape[1] - 1:
                str += " & "
        str += "\\\\\n"
    if brackets == "round":
        str += "\\end{pmatrix}\n"
    return str


def element_to_tex(element, frac_command=True):
    if isinstance(element, Fraction):
        str += "{} & ".format(fraction_to_tex(element, use_dolar=False), fraction_to_tex=frac_command)
    elif int(element) == element:
        str += "{:.0f} & ".format(element)
    else:
        str += "{} & ".format(element)


def operations_to_tex(items, frac_command=True):
    """

    :param items: a list of either matrices, numbers, or strings
    :return: a tex string
    """
    str = ""
    for i in items:
        if isinstance(i, six.string_types):
            str += i
        elif isinstance(i, np.ndarray):
            str += matrix_to_tex(i, frac_command=frac_command)
        elif isinstance(i, (int, float)):
            str += i
    return str


def create_equation(content_str):
    str = "\\begin{equation}\n\\begin{split}\n"
    str += content_str
    str += "\\end{split}\n\\end{equation}"
    return str


