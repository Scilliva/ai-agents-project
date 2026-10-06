"""Week 4 reference solution: the two tools and their schemas.

The implementations are unchanged from the starter. The schemas are the
completed answers to TODO 1 and TODO 2, and the comments say what each clause
is defending against rather than what it does.

These are defensible descriptions, not the only good ones. Read them as an
argument and disagree where you have measured something different.
"""

import ast
import operator
from typing import Any, Dict, List

import handbook

# ---------------------------------------------------------------------------
# Tool 1: search_services
# ---------------------------------------------------------------------------


def search_services(query: str, top_k: int = 3) -> List[dict]:
    """Return up to top_k handbook passages that match the query."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string of keywords")
    return handbook.search(query, top_k=top_k)


# TODO 1 answered.
#
# Four parts, in order, and each sentence is doing work.
#
#   Sentence 1 says what it does and over what. Naming the corpus stops the
#   model treating it as a web search.
#   Sentence 2 and 3 are the keyword instruction. The matcher scores token
#   overlap, so a full sentence dilutes the signal with stop words. Without
#   this line the model sends the user's question verbatim and retrieves the
#   wrong document about a third of the time.
#   Sentence 4 is the negative clause. Without it the model searches for
#   "26 times 8.50" on T-01, gets nothing, and then does the arithmetic in
#   its head, which is the failure the compute tool exists to prevent.
#   Sentence 5 describes the return shape, so the model knows a doc_id is
#   available to cite.
#   Sentence 6 defines the empty case AND says what to do about it. This is
#   the sentence that decides T-10. Without it, an empty result is a silence
#   the model fills with a plausible fee.

SEARCH_SCHEMA: Dict[str, Any] = {
    "name": "search_services",
    "description": (
        "Search the Remerbaach service handbook for opening hours, fees, "
        "forms, procedures, and contact details. "
        "Send KEYWORDS, not a full sentence: 'waste collection fee 240 litre' "
        "works, 'How much does a 240 litre bin cost per year?' does not. "
        "Use it for any factual question about a commune service. "
        "Do NOT use it for arithmetic, for translation, or to look up a "
        "person or an individual reference number: use the compute tool for "
        "arithmetic and answer directly when no handbook fact is needed. "
        "Returns a list of at most top_k passages, each with a doc_id, a "
        "title, and a verbatim snippet, best match first. "
        "An empty list means the handbook does not cover the question: say "
        "so plainly, name the service to contact, and never invent a figure."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": ("Two to six keywords in the language of the "
                                "handbook entry, for example "
                                "'building permit fee square metre'."),
            },
            # Constrained in the schema, not in prose. A top_k of 50 is now
            # impossible to request rather than merely discouraged.
            "top_k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "default": 3,
                "description": "How many passages to return. Three is enough.",
            },
        },
        "required": ["query"],
    },
}


# ---------------------------------------------------------------------------
# Tool 2: compute
# ---------------------------------------------------------------------------

_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
    ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CALLS = {"round": round, "min": min, "max": max, "abs": abs}


def _eval_node(node: ast.AST) -> float:
    """Walk a parsed expression, allowing only arithmetic."""

    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        return _BINARY[type(node.op)](_eval_node(node.left),
                                      _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval_node(node.operand))
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _CALLS and not node.keywords):
        return _CALLS[node.func.id](*[_eval_node(a) for a in node.args])
    raise ValueError(
        "only arithmetic is allowed: numbers, + - * / // % **, parentheses, "
        "and round, min, max, abs")


def compute(expression: str) -> float:
    """Evaluate one arithmetic expression and return a number."""

    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("expression must be a non-empty string")
    if len(expression) > 200:
        raise ValueError("expression too long, at most 200 characters")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"could not parse the expression: {exc.msg}") from exc
    return round(float(_eval_node(tree)), 6)


# TODO 2 answered.
#
# The worked example is the load-bearing part. A description that says
# "evaluates an arithmetic expression" produces arguments like
# "26 collections * 8.50 EUR", which the evaluator rejects, which costs a
# full extra step. One example of a valid argument fixes it.
#
# The second half is a policy rather than a mechanism: it tells the model
# that arithmetic done in prose is not acceptable here. The reason given in
# the description ("the result is checkable") is deliberate. A rule with a
# reason attached is followed more reliably than a bare instruction, and it
# is also the reason a human reviewer would accept.
#
# We chose not to promise that repeated calls are free. The tool is
# read-only and idempotent, so an extra call costs money and nothing else,
# but saying "call it as often as you like" measurably increases the number
# of calls, and every call is a step against the cap.

COMPUTE_SCHEMA: Dict[str, Any] = {
    "name": "compute",
    "description": (
        "Evaluate one arithmetic expression and return the number. "
        "The expression may contain numbers, + - * / // % **, parentheses, "
        "and round, min, max, abs. It may NOT contain units, words, currency "
        "symbols, or variable names. "
        "Example of a valid expression: '26 * 8.50 + 24.00'. "
        "Use it for ANY arithmetic on figures you retrieved from the "
        "handbook, instead of calculating in your answer, because a computed "
        "result can be checked and a number written out in prose cannot."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": ("Digits and operators only, for example "
                                "'40 * 2.50' or 'max(100, 150.00)'."),
            },
        },
        "required": ["expression"],
    },
}


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

REGISTRY = {
    "search_services": search_services,
    "compute": compute,
}

SCHEMAS = [SEARCH_SCHEMA, COMPUTE_SCHEMA]
SCHEMAS_SEARCH_ONLY = [SEARCH_SCHEMA]


if __name__ == "__main__":
    print(search_services("waste collection fee 240 litre"))
    print(compute("26 * 8.50 + 24.00"))
    try:
        compute("__import__('os').system('ls')")
    except ValueError as exc:
        print("rejected, as it should be:", exc)
