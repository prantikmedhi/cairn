from __future__ import annotations

import ast
import importlib
import re
from types import SimpleNamespace
from typing import Any


_EXPR_PATTERN = re.compile(r"\${{\s*(.*?)\s*}}")


class ExpressionError(ValueError):
    """Raised when expression cannot be evaluated safely."""


def render_value(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        matches = list(_EXPR_PATTERN.finditer(value))
        if not matches:
            rendered = _render_jinja_template(value, context)
            if rendered is not None:
                return rendered
            return value
        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            return evaluate_expression(matches[0].group(1), context)

        def replace(match: re.Match[str]) -> str:
            result = evaluate_expression(match.group(1), context)
            return "" if result is None else str(result)

        return _EXPR_PATTERN.sub(replace, value)
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    return value


def resolve_condition(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        if _EXPR_PATTERN.search(value):
            return render_value(value, context)
        return evaluate_expression(value, context)
    return value


def evaluate_expression(expression: str, context: dict[str, Any]) -> Any:
    tree = ast.parse(expression, mode="eval")
    namespace = {key: _to_namespace(value) for key, value in context.items()}
    return _eval_node(tree.body, namespace)


def _to_namespace(value: Any) -> Any:
    if isinstance(value, dict):
        return SimpleNamespace(**{key: _to_namespace(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_to_namespace(item) for item in value]
    return value


def _render_jinja_template(value: str, context: dict[str, Any]) -> str | None:
    if "{{" not in value and "{%" not in value:
        return None
    try:
        module = importlib.import_module("jinja2")
    except ImportError:
        return None
    template = module.Environment(autoescape=False).from_string(value)
    return template.render(context)


def _eval_node(node: ast.AST, namespace: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in namespace:
            return namespace[node.id]
        raise ExpressionError(f"Unknown name '{node.id}'")
    if isinstance(node, ast.Attribute):
        base = _eval_node(node.value, namespace)
        return getattr(base, node.attr)
    if isinstance(node, ast.Subscript):
        base = _eval_node(node.value, namespace)
        key = _eval_node(node.slice, namespace)
        return base[key]
    if isinstance(node, ast.List):
        return [_eval_node(item, namespace) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(item, namespace) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {_eval_node(key, namespace): _eval_node(value, namespace) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_node(node.operand, namespace)
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(value, namespace) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, namespace)
        for operator, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, namespace)
            if isinstance(operator, ast.Eq):
                ok = left == right
            elif isinstance(operator, ast.NotEq):
                ok = left != right
            elif isinstance(operator, ast.Gt):
                ok = left > right
            elif isinstance(operator, ast.GtE):
                ok = left >= right
            elif isinstance(operator, ast.Lt):
                ok = left < right
            elif isinstance(operator, ast.LtE):
                ok = left <= right
            else:
                raise ExpressionError(f"Unsupported comparator: {type(operator).__name__}")
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _eval_node(node.left, namespace) + _eval_node(node.right, namespace)
    raise ExpressionError(f"Unsupported expression node: {type(node).__name__}")
