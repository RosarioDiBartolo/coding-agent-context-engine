from importlib import import_module


def load_plugin(name: str):
    return import_module(name)


def load_optional_provider():
    import contextengine_missing_fixture_provider

    return contextengine_missing_fixture_provider
