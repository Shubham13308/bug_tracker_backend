from typing import Any


def get_changed_fields(
    old: dict[str, Any],
    new: dict[str, Any],
    exclude_fields: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Compare two dictionaries and return only changed fields.
    """

    if exclude_fields is None:
        exclude_fields = []

    changes: dict[str, dict[str, Any]] = {}

    keys = set(old.keys()) | set(new.keys())

    for key in keys:
        if key in exclude_fields:
            continue

        old_value = old.get(key)
        new_value = new.get(key)

        if old_value != new_value:
            changes[key] = {
                "old": old_value,
                "new": new_value,
            }

    return changes

def get_actor_name(current_user: dict) -> str:
    return current_user.get("full_name", current_user.get("name", "Unknown User"))
