import os
import yaml
from typing import Dict, Any

class Config:
    _instance = None
    _config_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls) -> None:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            cls._config_data = yaml.safe_load(f)

    @property
    def llm(self) -> Dict[str, str]:
        return self._config_data.get('llm', {})

    @property
    def prompts(self) -> Dict[str, str]:
        return self._config_data.get('prompts', {})

    @property
    def parser(self) -> Dict[str, Any]:
        return self._config_data.get('parser', {})

    def get_llm_config(self, key: str) -> str:
        return self.llm.get(key, '')

    def get_prompt(self, key: str) -> str:
        return self.prompts.get(key, '')

    def get_parser_config(self, key: str) -> Any:
        return self.parser.get(key)