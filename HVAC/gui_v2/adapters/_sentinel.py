"""
GUI Adapter Sentinel (CANONICAL)

This module must NEVER be imported at runtime.
If it is, the GUI ↔ Engine architecture contract
has been violated.

This error reports the exact import site.
"""

import inspect
import sys


def _raise_with_caller():
    stack = inspect.stack()

    # Skip this file + import machinery
    for frame in stack[2:]:
        filename = frame.filename
        lineno = frame.lineno
        code = frame.code_context[0].strip() if frame.code_context else ""

        # Ignore stdlib / importlib noise
        if "importlib" in filename or "_sentinel" in filename:
            continue

        raise RuntimeError(
            "\n🚨 FORBIDDEN GUI ADAPTER IMPORT 🚨\n"
            f"File: {filename}\n"
            f"Line: {lineno}\n"
            f"Code: {code}\n\n"
            "GUI adapters are forbidden.\n"
            "Use MainWindowV2 as the ONLY bridge."
        )


_raise_with_caller()
