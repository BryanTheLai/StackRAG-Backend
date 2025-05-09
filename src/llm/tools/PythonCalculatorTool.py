import pandas as pd
import numpy as np
import math
import io
import traceback
from google.genai import types as genai_types
import contextlib
from typing import List, Dict, Tuple, Any, Union # For pre-loading

PYTHON_CALCULATION_TOOL_DECLARATION_DATA = {
    "name": "execute_python_calculations",
    "description": (
        "Executes Python code for calculations. Pre-loaded and available directly: "
        "'math' module, 'pandas' (as 'pd'), 'numpy' (as 'np'). "
        "Common typing objects like `List`, `Dict`, `Tuple`, `Any`, `Union` are also pre-loaded and available directly. "
        "Do NOT import these. Your code MUST assign the final string result to a variable named 'calculation_result'. "
        "Print statements are also captured."
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
        self._safe_builtins = {
            'print': print, 'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'len': len, 'range': range, 'abs': abs, 'round': round,
            'sum': sum, 'min': min, 'max': max, 'sorted': sorted,
            'zip': zip, 'enumerate': enumerate, 'map': map, 'filter': filter,
            'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
            'repr': repr,
            'type': type,

            # Standard Exceptions that LLM might use in try-except blocks
            'Exception': Exception,
            'AttributeError': AttributeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'NameError': NameError,
            'TypeError': TypeError,
            'ValueError': ValueError,
            'ZeroDivisionError': ZeroDivisionError,
            'StopIteration': StopIteration,
        }
        # Globals for the exec environment, including the safe builtins and pre-loaded modules.
        self._execution_globals = {
            "__builtins__": self._safe_builtins,
            "math": math,
            "pd": pd,
            "np": np,
            "List": List,
            "Dict": Dict,
            "Tuple": Tuple,
            "Any": Any,
            "Union": Union,
        }

    @staticmethod
    def get_tool_declaration() -> genai_types.Tool:
        func_decl = genai_types.FunctionDeclaration(
            name=PYTHON_CALCULATION_TOOL_DECLARATION_DATA["name"],
            description=PYTHON_CALCULATION_TOOL_DECLARATION_DATA["description"],
            parameters=genai_types.Schema(**PYTHON_CALCULATION_TOOL_DECLARATION_DATA["parameters"])
        )
        return genai_types.Tool(function_declarations=[func_decl])

    def execute_code(self, python_code: str) -> str:
        if not isinstance(python_code, str):
            return "Error: Python code must be a non-empty string."

        local_vars: dict = {}
        stdout_capture = io.StringIO()
        output_parts: list[str] = []

        try:
            current_globals = dict(self._execution_globals)
            with contextlib.redirect_stdout(stdout_capture):
                exec(python_code, current_globals, local_vars)

            printed_output = stdout_capture.getvalue().strip()
            if printed_output:
                output_parts.append(f"Printed Output:\n{printed_output}")

            if 'calculation_result' in local_vars:
                result_val = local_vars['calculation_result']
                output_parts.append(f"Calculation Result:\n{str(result_val)}")
            elif not printed_output :
                output_parts.append("Note: Code executed. No 'calculation_result' was set and no print output was captured.")
            elif printed_output and 'calculation_result' not in local_vars:
                output_parts.append("Note: 'calculation_result' variable was not set by the code.")

        except Exception as e:
            tb_str = traceback.format_exc()
            max_tb_length = 1000
            if len(tb_str) > max_tb_length: # pragma: no cover
                tb_str = tb_str[:max_tb_length//2] + "\n... (traceback truncated) ...\n" + tb_str[-max_tb_length//2:]
            error_message = f"Python Execution Error:\n{type(e).__name__}: {str(e)}\nTraceback:\n{tb_str}"
            output_parts = [error_message]

        if not output_parts: # pragma: no cover
             return "No output produced by the code and no errors detected."

        return "\n\n".join(output_parts).strip()

# --- Test Script ---
if __name__ == "__main__":
    calculator = PythonCalculationTool()
    tool_declaration = PythonCalculationTool.get_tool_declaration()
    print("------- Tool Declaration -------")
    print(f"Name: {tool_declaration.function_declarations[0].name}")
    print(f"Description: {tool_declaration.function_declarations[0].description}")
    param_desc = tool_declaration.function_declarations[0].parameters.properties["python_code"].description #type: ignore
    print(f"Parameter Description for python_code: {param_desc}")


    print("\n------- Test Cases for execute_code -------")
    test_cases = [
        {
            "description": "Simple calculation with calculation_result",
            "code": "x = 10\ny = 20\ncalculation_result = f'The sum is {x + y}'"
        },
        {
            "description": "Using print statements",
            "code": "print('Starting calculation...')\nfor i in range(3):\n  print(f'Number: {i}')\nprint('Calculation finished.')"
        },
        {
            "description": "Using print and calculation_result",
            "code": "print('Processing data...')\ndata = {'a': 1, 'b': 2}\ncalculation_result = f'Data sum: {sum(data.values())}'"
        },
        {
            "description": "Using math module",
            "code": "radius = 5\narea = math.pi * math.pow(radius, 2)\ncalculation_result = f'Area of circle: {area:.2f}'"
        },
        {
            "description": "Using pandas and numpy",
            "code": (
                "data_list = [1, 2, 3, 4, 5]\n"
                "series = pd.Series(data_list)\n"
                "mean_val = np.mean(series).item()\n"
                "calculation_result = f'Mean of series: {mean_val}'"
            )
        },
        {
            "description": "Code with a runtime error (ZeroDivisionError)",
            "code": "x = 10\ny = 0\ncalculation_result = x / y"
        },
        {
            "description": "Code that does not set calculation_result and has no print",
            "code": "a = 1\nb = 2\nc = a + b"
        },
        {
            "description": "Code with print but no calculation_result",
            "code": "print('This is just a message.')\na = 5 * 5"
        },
        {
            "description": "Attempting to import a disallowed module (e.g., os)",
            "code": "import os\ncalculation_result = 'Should fail due to import error'"
        },
        {
            "description": "Attempting to use a disallowed builtin (e.g., open)",
            "code": "with open('test.txt', 'w') as f: f.write('hello')\ncalculation_result = 'Should fail due to disallowed builtin'"
        },
        {
            "description": "Empty code string",
            "code": ""
        },
        {
            "description": "Code with only comments",
            "code": "# This is just a comment\n# calculation_result = 'not set'"
        },
        {
            "description": "calculation_result is an integer",
            "code": "calculation_result = 12345"
        },
        {
            "description": "calculation_result is a float",
            "code": "calculation_result = 123.456"
        },
        {
            "description": "calculation_result is a list",
            "code": "my_list = [1, 'apple', 3.14]\ncalculation_result = my_list"
        },
        {
            "description": "calculation_result is a dictionary",
            "code": "my_dict = {'name': 'Test', 'value': 100}\ncalculation_result = my_dict"
        },
        {
            "description": "calculation_result is None",
            "code": "calculation_result = None"
        },
        {
            "description": "calculation_result is a very long string",
            "code": "calculation_result = 'A' * 2000"
        },
        {
            "description": "Attempt to redefine pre-loaded 'pd' and use it (AttributeError now catchable)",
            "code": (
                "print(f'Original pd type: {type(pd)}')\n"
                "pd = 'This is not pandas'\n"
                "print(f'Redefined pd: {pd}')\n"
                "try:\n"
                "  s = pd.Series([1,2])\n"
                "  calculation_result = 'Error: AttributeError was expected but not raised for pd.Series'\n"
                "except AttributeError as e:\n" # This should now work
                "  calculation_result = f'Caught expected error: {e}'\n"
                "except Exception as e_other:\n"
                "  calculation_result = f'Caught UNEXPECTED error: {type(e_other).__name__}: {e_other}'"
            )
        },
        {
            "description": "Code defines and uses a local function",
            "code": (
                "def my_adder(a, b):\n"
                "  return a + b\n"
                "result = my_adder(10, 15)\n"
                "calculation_result = f'Function result: {result}'"
            )
        },
        {
            "description": "Accessing locals() builtin (NameError catchable)",
            "code": (
                "try:\n"
                "  l = locals()\n" # locals() itself is not in _safe_builtins, will raise NameError
                "  calculation_result = 'Error: locals() should not be available or NameError not caught'\n"
                "except NameError as e:\n" # This should now work to catch the NameError from calling locals()
                "  calculation_result = f'Caught expected NameError for locals(): {e}'\n"
                "except Exception as e_other:\n"
                "  calculation_result = f'Caught UNEXPECTED error for locals(): {type(e_other).__name__}: {e_other}'"
            )
        },
        {
            "description": "Using pre-available typing hints (List, Dict)",
            "code": (
                "def process_data(data: Dict[str, int]) -> List[str]:\n"
                "    results: List[str] = []\n"
                "    for k, v in data.items():\n"
                "        results.append(f'{k}: {v*2}')\n"
                "    return results\n"
                "my_dictionary: Dict[str, int] = {'a': 1, 'b': 20}\n"
                "processed_list: List[str] = process_data(my_dictionary)\n"
                "calculation_result = f'Processed: {processed_list}'"
            )
        },
        {
            "description": "Code with non-ASCII characters (UTF-8)",
            "code": "# Comment: αβγδε\ntext = '你好世界'\nprint(f'Chinese text: {text}')\ncalculation_result = f'Unicode test: {text} ✔'"
        },
        {
            "description": "Very long print output (e.g., 50 lines of 100 chars)",
            "code": "for i in range(50):\n  print(f'Line {i}: ' + ('*' * 100))\n# No calculation_result"
        },
        {
            "description": "Prints, then errors before calculation_result",
            "code": "print('About to perform a risky operation...')\nx = 1 / 0\ncalculation_result = 'This should not be reached'"
        },
        {
            "description": "Sets calculation_result, then errors",
            "code": "calculation_result = 'Initial value set'\nprint(f'Current result: {calculation_result}')\ny = some_undefined_variable"
        },
        {
            "description": "Syntax error in code",
            "code": "calculation_result = 'Syntax Error Test'\ndef my_func("
        }
    ]

    for i, test_case in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {test_case['description']} ---")
        print(f"Code to execute:\n```python\n{test_case['code']}\n```")
        result = calculator.execute_code(test_case['code'])
        print(f"Output:\n{result}")

    print("\n--- Test Case: Invalid input type ---")
    invalid_input_result = calculator.execute_code(123) # type: ignore
    print(f"Output for non-string input (123):\n{invalid_input_result}")
    invalid_input_result_none = calculator.execute_code(None) # type: ignore
    print(f"Output for non-string input (None):\n{invalid_input_result_none}")

    print("\n--- Verification: Check if tool's 'pd' is modified globally ---")
    test_pd_integrity_code = "series = pd.Series([10, 20])\ncalculation_result = f'Pandas still works: {series.sum()}'"
    print(f"Code to execute after 'pd' redefinition attempt:\n```python\n{test_pd_integrity_code}\n```")
    integrity_check_result = calculator.execute_code(test_pd_integrity_code)
    print(f"Output:\n{integrity_check_result}")
    print(f"Type of 'pd' in calculator._execution_globals after tests: {type(calculator._execution_globals['pd'])}")
    print(f"Type of 'List' in calculator._execution_globals after tests: {calculator._execution_globals['List']}")