import pandas as pd
import numpy as np
import math
import io
import traceback
from google.genai import types as genai_types
import contextlib
from typing import List, Dict, Tuple, Any, Union

PYTHON_CALCULATION_TOOL_DECLARATION_DATA: Dict = {
    "name": "execute_python_calculations",
    "description": (
        "Executes Python code for calculations. Pre-loaded and available directly: "
        "'math' module, 'pandas' (as 'pd'), 'numpy' (as 'np'). "
        "Common typing objects like `List`, `Dict`, `Tuple`, `Any`, `Union` are also pre-loaded and available directly. "
        "The variable '__name__' is set to '__main__'. "
        "Your code MUST assign the final string result to a variable named 'calculation_result'. "
        "Print statements are also captured. Class definitions, 'eval()', and 'globals()' calls are not supported."
        " You can use 'import' statements for standard Python libraries if needed, but core modules like 'math', 'pd', 'np' are already available."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "python_code": {
                "type": "string",
                "description": (
                    "A string containing the Python code to execute. "
                    "Use 'pd' for pandas, 'np' for numpy, 'math' for the math module, "
                    "and typing objects like `List`, `Dict` directly without importing them. "
                    "The final result must be a string assigned to 'calculation_result'."
                )
            }
        },
        "required": ["python_code"]
    }
}

class PythonCalculationTool:
    def __init__(self) -> None:
        self._original_math_pi = math.pi

        self._safe_builtins = {
            '__import__': __import__,
            'print': print, 'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'len': len, 'range': range, 'abs': abs, 'round': round,
            'sum': sum, 'min': min, 'max': max, 'sorted': sorted,
            'zip': zip, 'enumerate': enumerate, 'map': map, 'filter': filter,
            'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
            'repr': repr,
            'type': type,
            'Exception': Exception, 'AttributeError': AttributeError, 'KeyError': KeyError,
            'IndexError': IndexError, 'NameError': NameError, 'TypeError': TypeError,
            'ValueError': ValueError, 'ZeroDivisionError': ZeroDivisionError,
            'StopIteration': StopIteration, 'RecursionError': RecursionError,
        }
        self._execution_globals = {
            "__builtins__": self._safe_builtins,
            "math": math,
            "pd": pd,
            "np": np,
            "List": List, "Dict": Dict, "Tuple": Tuple, "Any": Any, "Union": Union,
            "__name__": "__main__",
        }

    @staticmethod
    def get_tool_declaration_data() -> Dict:
        """ 
        Returns the Gemini tool declaration for the execute_python_calculations function.
        """
        return PYTHON_CALCULATION_TOOL_DECLARATION_DATA

    def execute_python_calculations(self, python_code: str) -> str:
        if not isinstance(python_code, str):
            return "Error: Python code must be a non-empty string."

        local_vars: dict = {}
        stdout_capture = io.StringIO()
        output_parts: list[str] = []
        current_globals = dict(self._execution_globals)

        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(python_code, current_globals, local_vars)
            printed_output = stdout_capture.getvalue().strip()
            if printed_output:
                output_parts.append(f"Printed Output:\n{printed_output}")
            if 'calculation_result' in local_vars:
                result_val = local_vars['calculation_result']
                output_parts.append(f"Calculation Result:\n{str(result_val)}")
            elif not printed_output:
                output_parts.append("Note: Code executed. No 'calculation_result' was set and no print output was captured.")
            elif printed_output and 'calculation_result' not in local_vars:
                output_parts.append("Note: 'calculation_result' variable was not set by the code.")
        except Exception as e:
            tb_str = traceback.format_exc()
            max_tb_length = 1000
            if len(tb_str) > max_tb_length: 
                tb_str = tb_str[:max_tb_length//2] + "\n... (traceback truncated) ...\n" + tb_str[-max_tb_length//2:]
            error_message = f"Python Execution Error:\n{type(e).__name__}: {str(e)}\nTraceback:\n{tb_str}"
            output_parts = [error_message]
        if not output_parts:
             return "No output produced by the code and no errors detected."
        return "\n\n".join(output_parts).strip()