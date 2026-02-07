import json
import os
from typing import Dict
from datetime import datetime

class TokenManager:
    """
    Manages tracking of AI token usage and persists it to a JSON file.
    """
    def __init__(self, storage_file="token_usage.json"):
        self.storage_file = storage_file
        self.usage_data = self._load_usage()

    def _load_usage(self) -> Dict:
        """Loads usage data from the JSON file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading token usage: {e}")
                return self._init_usage_structure()
        return self._init_usage_structure()

    def _init_usage_structure(self) -> Dict:
        """Initializes an empty usage structure."""
        return {
            "total_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_requests": 0,
            "models": {},
            "last_updated": None
        }

    def add_usage(self, model_name: str, input_tokens: int, output_tokens: int):
        """
        Records token usage for a specific model call.
        """
        # Update Global Totals
        self.usage_data["total_input_tokens"] += input_tokens
        self.usage_data["total_output_tokens"] += output_tokens
        self.usage_data["total_tokens"] += (input_tokens + output_tokens)
        self.usage_data["total_requests"] += 1
        self.usage_data["last_updated"] = datetime.now().isoformat()

        # Update Model-Specific Stats
        if model_name not in self.usage_data["models"]:
            self.usage_data["models"][model_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "requests": 0
            }
        
        self.usage_data["models"][model_name]["input_tokens"] += input_tokens
        self.usage_data["models"][model_name]["output_tokens"] += output_tokens
        self.usage_data["models"][model_name]["total_tokens"] += (input_tokens + output_tokens)
        self.usage_data["models"][model_name]["requests"] += 1

        self._save_usage()

    def _save_usage(self):
        """Persists usage data to the JSON file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=4)
        except Exception as e:
            print(f"Error saving token usage: {e}")

    def get_usage(self) -> Dict:
        """Returns the current usage statistics."""
        return self.usage_data
