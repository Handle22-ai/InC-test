"""Small, side-effect-free predicate vocabulary for the normalized contract."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def validate(expression: dict) -> None:
    """Reject unsupported syntax before short-circuit evaluation can hide it."""
    if not isinstance(expression, dict):
        raise ValueError("Predicate must be a structured expression")
    operator = expression.get("operator")
    if operator in {"all", "any"}:
        if set(expression) != {"operator", "conditions"}:
            raise ValueError("Invalid compound predicate")
        children = expression["conditions"]
        if not isinstance(children, list) or not children:
            raise ValueError("Compound predicate requires nonempty conditions")
        for child in children:
            validate(child)
        return
    if operator == "some":
        if set(expression) != {"operator", "field", "condition"} or not isinstance(
            expression["field"], str
        ):
            raise ValueError("Invalid array predicate")
        validate(expression["condition"])
        return
    if operator == "not":
        if set(expression) != {"operator", "condition"}:
            raise ValueError("Invalid negated predicate")
        validate(expression["condition"])
        return
    operands = {
        "eq": ("value", "value_field"),
        "in": ("values", "values_field"),
        "contains_any": ("values", "values_field"),
        "contains_only": ("values", "values_field"),
        "after": ("value_field",),
    }
    if operator not in operands:
        raise ValueError("Unsupported predicate operator: " + str(operator))
    alternatives = operands[operator]
    selected = [key for key in alternatives if key in expression]
    if len(selected) != 1 or set(expression) != {"operator", "field", selected[0]}:
        raise ValueError("Predicate requires exactly one supported operand")
    for key in ["field", *[k for k in selected if k.endswith("_field")]]:
        path = expression[key]
        if not isinstance(path, str) or not path or any(not p for p in path.split(".")):
            raise ValueError("Predicate field must be a nonempty dotted path")
    if "values" in expression and not isinstance(expression["values"], list):
        raise ValueError("Predicate values must be an array")


def field(context: dict, path: str):
    value = context
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError("Unavailable predicate field: " + path)
        value = value[part]
    return value


def equal(left, right) -> bool:
    """JSON equality, including nested boolean/number distinctions."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    return left == right


def evaluate(expression: dict, context: dict) -> bool:
    operator = expression["operator"]
    if operator == "all":
        return all(evaluate(child, context) for child in expression["conditions"])
    if operator == "any":
        return any(evaluate(child, context) for child in expression["conditions"])
    if operator == "some":
        try:
            members = field(context, expression["field"])
        except ValueError:
            members = []
        if not isinstance(members, list):
            raise ValueError("Array predicate requires an array")
        return any(evaluate(expression["condition"], {**context, "item": item}) for item in members)
    if operator == "not":
        return not evaluate(expression["condition"], context)
    left = field(context, expression["field"])
    right: Any = (
        field(context, expression["value_field"])
        if "value_field" in expression
        else field(context, expression["values_field"])
        if "values_field" in expression
        else expression.get("value", expression.get("values"))
    )
    if operator == "eq":
        return equal(left, right)
    if operator == "in":
        return any(equal(left, value) for value in right)
    if operator == "contains_any":
        return any(equal(value, item) for value in left for item in right)
    if operator == "contains_only":
        return all(any(equal(value, item) for item in right) for value in left)
    if operator == "after":
        return datetime.fromisoformat(left) > datetime.fromisoformat(right)
    raise ValueError("Unsupported predicate operator: " + str(operator))
