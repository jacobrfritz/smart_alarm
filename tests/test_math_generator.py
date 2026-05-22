import re

from smart_alarm.math_generator import BasicMathProblemGenerator


def test_generate_problem_format() -> None:
    generator = BasicMathProblemGenerator()

    # Run multiple times to verify all operation types are generated and accurate
    operations_observed = set()

    for _ in range(200):
        question, answer = generator.generate_problem()

        # Check matching question format
        assert question.startswith("What is ")
        assert question.endswith("?")

        # Extract formula part
        formula = question[8:-1]

        # Find which operator was generated
        matched = re.search(r"([\+\-\*/])", formula)
        assert matched is not None
        operator = matched.group(1)
        operations_observed.add(operator)

        # Parse terms
        terms = [int(x) for x in re.split(r"\s*[\+\-\*/]\s*", formula)]
        assert len(terms) == 2
        a, b = terms[0], terms[1]

        # Verify math correctness
        if operator == "+":
            assert answer == a + b
            assert 100 <= a <= 999
            assert 100 <= b <= 999
        elif operator == "-":
            assert answer == a - b
            assert a >= b
            assert 100 <= a <= 999
            assert 100 <= b <= 999
        elif operator == "*":
            assert answer == a * b
            assert 12 <= a <= 99
            assert 12 <= b <= 99
        elif operator == "/":
            assert answer == a / b
            # Division answer must be an exact integer quotient
            assert int(answer) == answer
            assert a % b == 0
            assert 11 <= b <= 50
            assert 10 <= answer <= 80

    # Ensure all four mathematical operators are generated over the test distribution
    assert operations_observed == {"+", "-", "*", "/"}
