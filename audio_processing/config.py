"""
Audio Processing Configuration

This module contains configurations for the audio processing features.
"""
import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AudioProcessingConfig:
    """Configuration settings for audio processing features."""
    # Master switch to enable/disable all processing
    enabled: bool = True
    
    # Output directory (None means same as input)
    output_directory: Optional[str] = None
    
    # Feature toggles
    enable_noise_reduction: bool = True
    
    # Processing parameters
    noise_reduction_strength: float = 0.7  # 0.0 to 1.0
    
    # Output file naming
    preserve_original: bool = True
    output_suffix: str = "_enhanced"
    
    # Advanced settings
    processing_threads: int = 2
    max_memory_usage_mb: int = 1024
    
    @classmethod
    def load(cls, config_path=None):
        """Load configuration from a JSON file."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "audio_processing_config.json")
        
        if not os.path.exists(config_path):
            logging.warning(f"Configuration file not found at {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            
            # Create a new config with default values
            config = cls()
            
            # Update with values from the file
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            logging.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            return cls()
    
    def save(self, config_path=None):
        """Save configuration to a JSON file."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "audio_processing_config.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(asdict(self), f, indent=4)
            logging.info(f"Configuration saved to {config_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False 