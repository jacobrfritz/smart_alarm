import random

from .interfaces import MathProblemGeneratorInterface


class BasicMathProblemGenerator(MathProblemGeneratorInterface):
    """Generates heavy arithmetic problems that require a calculator."""

    def generate_problem(self) -> tuple[str, int]:
        """Generates a math problem (+, -, *, /) and returns its exact integer answer.

        Guarantees that division problems evaluate to precise integers.
        """
        operation = random.choice(["*", "/"])

        if operation == "*":
            # Multiply two 2-3 digit numbers
            a = random.randint(10, 999)
            b = random.randint(10, 999)
            return f"What is {a} * {b}?", a * b

        else:  # operation == "/"
            # Division that yields a whole number, where operands are 2-3 digit numbers
            while True:
                divisor = random.randint(10, 999)
                quotient = random.randint(2, 99)
                dividend = divisor * quotient
                if 10 <= dividend <= 999 and 10 <= divisor <= 999:
                    return f"What is {dividend} / {divisor}?", quotient

