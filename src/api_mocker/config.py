import os
import json
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None
try:
    import toml
except ImportError:
    toml = None

class ConfigLoader:
    @staticmethod
    def load(path: str) -> Dict[str, Any]:
        ext = os.path.splitext(path)[-1].lower()
        with open(path, 'r') as f:
            if ext in ['.yaml', '.yml'] and yaml:
                config = yaml.safe_load(f)
            elif ext == '.json':
                config = json.load(f)
            elif ext == '.toml' and toml:
                config = toml.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {ext}")
        return ConfigLoader._apply_env_overrides(config)

    @staticmethod
    def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder: implement environment variable overrides
        return config 