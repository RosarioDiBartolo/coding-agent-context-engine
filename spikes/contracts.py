"""Step 0 result contracts. Coordinates and hashes belong to a snapshot."""
from dataclasses import asdict, dataclass
import hashlib
from math import isfinite
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class ProbeResult:
    provider: str
    operation: str
    status: Literal['ok', 'blocked', 'error', 'unsupported']
    version: str | None = None
    data: Any = None
    error: dict | None = None
    elapsed_ms: float | None = None
    schema_version: int = 1

    def __post_init__(self):
        if self.status not in {'ok', 'blocked', 'error', 'unsupported'}:
            raise ValueError('Unknown probe status')
        if self.status == 'ok' and (self.error is not None or self.data is None):
            raise ValueError('Success requires data and no error')
        if self.status != 'ok' and (self.error is None or self.data is not None):
            raise ValueError('Non-success requires an error and no data')
        if self.elapsed_ms is not None and (not isfinite(self.elapsed_ms) or self.elapsed_ms < 0):
            raise ValueError('Invalid elapsed time')

    def to_dict(self):
        return asdict(self)


def normalize_pydeps(raw, repo: Path):
    """Normalize provider output without inventing paths or call edges."""
    if not isinstance(raw, dict):
        raise ValueError('pydeps output must be an object')
    repo = repo.resolve()
    nodes, edges = {}, set()
    for module, item in sorted(raw.items()):
        if not isinstance(item, dict):
            raise ValueError('Invalid pydeps node')
        relative, resolution = None, 'unresolved'
        path = item.get('path')
        if path:
            path = Path(path)
            path = (path if path.is_absolute() else repo / path).resolve()
            if path.is_file():
                if path.is_relative_to(repo):
                    relative, resolution = path.relative_to(repo).as_posix(), 'local'
                else:
                    resolution = 'external'
        nodes[module] = {'module': module, 'path': relative, 'resolution': resolution}
        for key in ['imports', 'imported_by']:
            values = item.get(key, [])
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise ValueError(f'Invalid {key}')
            for value in values:
                edges.add((module, value) if key == 'imports' else (value, module))
    for source, target in edges:
        for module in [source, target]:
            nodes.setdefault(module, {'module': module, 'path': None, 'resolution': 'unresolved'})
    return {'nodes': [nodes[k] for k in sorted(nodes)],
            'edges': [{'type': 'imports', 'source': a, 'target': b} for a, b in sorted(edges)],
            'limitations': ['Dynamic targets may be absent', 'No call graph',
                            'Missing path does not prove external status']}


def normalize_jev(raw):
    if not isinstance(raw, dict):
        raise ValueError('Jev response must be an object')
    answer = raw.get('answers', {}).get('relevant', {})
    p = answer.get('noul')
    if answer.get('type') != 'noul' or isinstance(p, bool) or not isinstance(p, (int, float)):
        raise ValueError('Missing typed Noul answer')
    if not isfinite(p) or not 0 <= p <= 1:
        raise ValueError('Invalid Noul probability')
    return {'probability_yes': p, 'model': raw.get('model'),
            'usage': raw.get('usage'), 'request_id': raw.get('request_id')}


def normalize_symbols(raw, repo: Path, *, acquisition: str):
    """Preserve provider locators; a search candidate is not a proved definition."""
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError('Symbol response must be a list or object')
    symbols = []
    root = repo.resolve()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError('Invalid symbol entry')
        name, relative = item.get('name_path'), item.get('relative_path')
        if not isinstance(name, str) or not isinstance(relative, str):
            raise ValueError('Symbol locator is missing')
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Symbol refers to unavailable file')
        location = item.get('body_location')
        if not isinstance(location, dict):
            raise ValueError('Symbol range missing')
        start, end = location.get('start_line'), location.get('end_line')
        if (type(start) is not int or type(end) is not int or start < 0 or end < start):
            raise ValueError('Invalid symbol range')
        symbols.append({'provider': 'serena', 'locator': {'path': relative, 'name_path': name},
                        'provider_id': None, 'kind': item.get('kind'),
                        'range': {'start_line': start, 'end_line': end, 'base': 0, 'end_inclusive': True},
                        'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'acquisition': acquisition, 'body': item.get('body')})
    return symbols
