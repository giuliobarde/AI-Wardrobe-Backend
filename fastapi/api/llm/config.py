import json
import logging
from typing import Dict, List, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIConfig:
    """Configuration management class with JSON file loading"""
    _instance = None
    _config = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of AIConfig"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from JSON file"""
        # Path to the config file, relative to this script
        config_path = Path(__file__).parent / 'config' / 'ai_config.json'
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
                logger.info(f"AI config loaded successfully from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Provide a minimal default config in case file loading fails
            self._config = {
                "allowed_occasions": ["all occasions"],
                "occasion_config": {"all occasions": {"items": [], "rules": "", "strictness": "Low", "description": ""}},
                "occasion_temperature": {"all occasions": 0.5}
            }
    
    def get_allowed_occasions(self) -> List[str]:
        """Get list of all allowed occasions"""
        return self._config.get("allowed_occasions", ["all occasions"])
    
    def get_occasion_config(self, occasion: str = None) -> Dict[str, Any]:
        """Get configuration for a specific occasion or all occasions"""
        occasion_configs = self._config.get("occasion_config", {})
        if occasion:
            return occasion_configs.get(occasion, occasion_configs.get("all occasions", {}))
        return occasion_configs
    
    def get_occasion_temperature(self, occasion: str) -> float:
        """Get temperature setting for a specific occasion"""
        temp_map = self._config.get("occasion_temperature", {})
        return temp_map.get(occasion, 0.5)


# Initialize the config
ai_config = AIConfig.get_instance()