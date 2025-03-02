import ast

class SyntaxChecker:
    def __init__(self):
        pass

    def check_syntax(self, stacktrace: str, student_solution: str) -> tuple[bool, str]:
        try:
            ast.parse(student_solution)
        except IndentationError as e:
            return True, f"Ошибка отступов: {str(e)}"
        except SyntaxError as e:
            return True, str(e)

        stacktrace = stacktrace.lower() if stacktrace else ""
        if "indent" in stacktrace:
            return True, stacktrace
        elif stacktrace:
            return True, stacktrace
        return False, "Синтаксических ошибок не найдено."