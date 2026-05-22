import random

from .interfaces import MathProblemGeneratorInterface


class BasicMathProblemGenerator(MathProblemGeneratorInterface):
    """Generates heavy arithmetic problems that require a calculator."""

    def generate_problem(self) -> tuple[str, int]:
        """Generates a math problem (+, -, *, /) and returns its exact integer answer.

        Guarantees that division problems evaluate to precise integers.
        """
        operation = random.choice(["+", "-", "*", "/"])

        if operation == "+":
            # Add two 3-digit numbers
            a = random.randint(100, 999)
            b = random.randint(100, 999)
            return f"What is {a} + {b}?", a + b

        elif operation == "-":
            # Subtract two 3-digit numbers, ensuring positive result
            a = random.randint(100, 999)
            b = random.randint(100, 999)
            num1, num2 = max(a, b), min(a, b)
            return f"What is {num1} - {num2}?", num1 - num2

        elif operation == "*":
            # Multiply two double-digit numbers
            a = random.randint(12, 99)
            b = random.randint(12, 99)
            return f"What is {a} * {b}?", a * b

        else:  # operation == "/"
            # Division that yields a whole number
            divisor = random.randint(11, 50)
            quotient = random.randint(10, 80)
            dividend = divisor * quotient
            return f"What is {dividend} / {divisor}?", quotient
