# jarvis_code_sandbox.py - Code Execution Sandbox
# Safely executes Python code snippets and displays output

import subprocess
import sys
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json
import time


class CodeSandboxHandler:
    """
    Provides safe execution of Python code snippets.
    Runs code in isolated subprocess to prevent system damage.
    """

    # Dangerous modules that should be blocked
    BLOCKED_IMPORTS = {
        'os', 'subprocess', 'socket', 'urllib',
        'requests', 'shutil', 'glob'
    }

    def __init__(self, max_timeout: int = 30, max_lines: int = 100):
        self.max_timeout = max_timeout
        self.max_lines = max_lines
        self.execution_history = []

    def _extract_imports(self, code: str) -> set:
        """Extract all imported module names from code."""
        imports = set()
        import re
        # Regex to find 'import X' or 'from X import Y'
        pattern = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import|import\s+((?:[.\w]+(?:,\s*)?)+))", re.MULTILINE)
        for match in pattern.finditer(code):
            if match.group(1):  # from X import Y
                imports.add(match.group(1).split('.')[0])
            elif match.group(2):  # import X, Y, Z
                modules = match.group(2).split(',')
                for mod in modules:
                    imports.add(mod.strip().split('.')[0])
        return imports

    def _check_dangerous_operations(self, code: str) -> Tuple[bool, Optional[str]]:
        """Check if code contains dangerous operations."""
        # Check for blocked imports
        used_imports = self._extract_imports(code)
        blocked = used_imports.intersection(self.BLOCKED_IMPORTS)
        if blocked:
            return False, f"Dangerous import blocked: '{next(iter(blocked))}'"

        code_lower = code.lower()

        dangerous_patterns = [
            ('os.system', 'Direct system commands'),
            ('subprocess', 'subprocess module'),
            ('shutil.rmtree', 'File deletion'),
            ('os.remove', 'File deletion'),
            ('exec(', 'Dynamic code execution'),
            ('eval(', 'Dynamic code evaluation'),
            ('__import__', 'Dynamic imports'),
            ('open(', 'File operations (use restricted APIs)'),
            ('socket.socket', 'Network sockets'),
            ('requests.get', 'HTTP requests'),
        ]

        for pattern, description in dangerous_patterns:
            if pattern.lower() in code_lower:
                return False, f"Dangerous operation blocked: {description}"

        return True, None

    def execute_code(
        self,
        code: str,
        timeout: Optional[int] = None,
        allow_dangerous: bool = False
    ) -> Dict[str, Any]:
        """
        Execute Python code in a sandbox.
        
        Args:
            code: Python code to execute
            timeout: Timeout in seconds (default: max_timeout)
            allow_dangerous: Allow dangerous operations (use with caution)
            
        Returns:
            Dict with execution result
        """
        if timeout is None:
            timeout = self.max_timeout
        temp_file = None
        
        # Validation
        if len(code.strip()) == 0:
            return {"success": False, "error": "Empty code"}
        
        if code.count('\n') > self.max_lines:
            return {
                "success": False,
                "error": f"Code exceeds maximum lines ({self.max_lines})"
            }
        
        # Safety check
        if not allow_dangerous:
            safe, error_msg = self._check_dangerous_operations(code)
            if not safe:
                return {"success": False, "error": error_msg}
        
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                temp_file = f.name
                f.write(code)
            
            # Execute in subprocess
            start_time = time.time()
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                execution_time = time.time() - start_time
                
                result = {
                    "success": process.returncode == 0,
                    "output": stdout.strip(),
                    "errors": stderr.strip(),
                    "execution_time": round(execution_time, 3),
                    "return_code": process.returncode
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                output, errors = process.communicate()
                result = {
                    "success": False,
                    "error": f"Code execution timeout after {timeout} seconds",
                    "output": output.strip() if output else "",
                    "errors": errors.strip() if errors else ""
                }
            
        except Exception as e:
            result = {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
        
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except Exception:
                pass
        
        # Store in history
        self.execution_history.append({
            "code": code,
            "result": result,
            "timestamp": time.time()
        })
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        return result
    
    def execute_python_snippet(self, snippet: str, **kwargs) -> str:
        """
        Execute code and return formatted output for chat.
        
        Args:
            snippet: Python code
            **kwargs: Additional arguments for execute_code
            
        Returns:
            Formatted output string
        """
        result = self.execute_code(snippet, **kwargs)
        
        if result["success"]:
            if result["output"]:
                return f"```\n{result['output']}\n```\n(Execution time: {result['execution_time']}s)"
            else:
                return f"(Code executed successfully in {result['execution_time']}s)"
        else:
            error_msg = result.get("error", "Unknown error")
            errors = result.get("errors", "")
            if errors:
                return f"Error: {error_msg}\n```\n{errors}\n```"
            else:
                return f"Error: {error_msg}"
    
    def get_execution_history(self, limit: int = 10) -> list:
        """Get recent code executions."""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history = []
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Check code for syntax and safety issues.
        
        Args:
            code: Python code to validate
            
        Returns:
            Validation result dict
        """
        # Check syntax
        try:
            compile(code, '<string>', 'exec')
            syntax_valid = True
            syntax_error = None
        except SyntaxError as e:
            syntax_valid = False
            syntax_error = str(e)
        
        # Check safety
        safe, safety_msg = self._check_dangerous_operations(code)
        
        # Check imports
        imports = self._extract_imports(code)
        
        return {
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error,
            "is_safe": safe,
            "safety_message": safety_msg,
            "imports": list(imports),
            "line_count": len(code.split('\n'))
        }


# Example usage
if __name__ == "__main__":
    sandbox = CodeSandboxHandler()
    
    # Test code
    test_code = """
x = 5
y = 10
print(f"Sum: {x + y}")
result = [i**2 for i in range(5)]
print(f"Squares: {result}")
"""
    
    result = sandbox.execute_code(test_code)
    print("Execution Result:")
    print(json.dumps(result, indent=2))
    
    # Validate dangerous code
    dangerous_code = "import os; os.system('ls')"
    validation = sandbox.validate_code(dangerous_code)
    print("\nValidation Result:")
    print(json.dumps(validation, indent=2))
