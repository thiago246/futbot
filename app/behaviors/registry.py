from app.behaviors import primitives
from app.core.exceptions import BehaviorError

PRIMITIVES = {
    "correr_hacia": primitives.correr_hacia,
    "patear": primitives.patear,
    "robar_pelota_jugador": primitives.robar_pelota_jugador,
}


def load_behavior(code: str):
    """Compile the behavior code and return its `decidir` function."""
    ns = {"__builtins__": {}, **PRIMITIVES}
    try:
        exec(compile(code, "<behavior>", "exec"), ns)
    except Exception as e:
        raise BehaviorError(f"Failed to load behavior: {e}") from e
    decide = ns.get("decidir")
    if not callable(decide):
        raise BehaviorError("Behavior code must define decidir(contexto)")
    return decide