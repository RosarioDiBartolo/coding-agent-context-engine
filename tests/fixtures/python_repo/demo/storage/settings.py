import yaml


def load_settings(text: str) -> dict:
    """A real installed external dependency for the pydeps probe."""
    return yaml.safe_load(text)
