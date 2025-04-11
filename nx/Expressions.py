def format_exp(name, type='number', value=0, unit=''):
    """
    Formats an expression string for NX.

    Args:
        name (str): The name of the expression.
        type (str, optional): The type of the expression ('number', 'int', 'str', 'bool', 'pt', 'vt', 'lt'). Defaults to 'number'.
        value (any, optional): The value or formula of the expression. Defaults to 0. For 'pt', 'vt', and 'lt', provide a list.
        unit (str, optional): The unit of the expression. Defaults to ''.

    Returns:
        str: The formatted expression string.
    """

    unit_str = f"[{unit}]" if unit else ""
    type_str = ""
    formula = str(value)  # Default formula is the string representation of the value

    if type == 'number' or type == 'int':
        pass  # No type prefix needed for numbers and integers
    elif type == 'str':
        type_str = '(String) '
    elif type == 'bool':
        type_str = '(Boolean) '  # Corrected spelling
    elif type == 'pt':
        type_str = '(Point) '
        if isinstance(value, list):
            formula = f"point({', '.join(map(str, value))})"
        else:
            formula = 'point()' #handles the case where value is not a list.
    elif type == 'vt':
        type_str = '(Vector) '
        if isinstance(value, list):
            formula = f"vector({', '.join(map(str, value))})"
        else:
            formula = 'vector()' #handles the case where value is not a list.
    elif type == 'lt':
        type_str = '(List) '
        if isinstance(value, list):
             formula = f"{{{', '.join(map(str, value))}}}"
        else:
            formula = '{}' #handles the case where value is not a list.
    elif type not in ['number', 'int', 'str', 'bool', 'pt', 'vt', 'lt']:
        raise ValueError(f"Invalid expression type: {type}") #raise error for invalid type

    return f"{type_str}{unit_str}{name}={formula}"


def write_exp_file(expressions, filename):
    """
    Writes a list of formatted expression strings to an .exp file.

    Args:
        expressions (list): A list of formatted expression strings.
        filename (str): The filename (without extension).
    """

    with open(f"{filename}.exp", "w") as f:
        f.write("// Version:  3\n")
        f.writelines(expression + "\n" for expression in expressions)


def write_txt_file(lines, filename):
    """
    Writes a list of strings to a .txt file.

    Args:
        lines (list): A list of strings to write.
        filename (str): The filename (without extension).
    """

    with open(f"{filename}.txt", "w") as f:
        f.writelines(line + "\n" for line in lines)