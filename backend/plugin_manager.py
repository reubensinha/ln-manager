# TODO: Implement plugin loading and management
from ast import mod
import subprocess
import os
import importlib
import re
import sys
from fastapi import dependencies
import yaml
from pathlib import Path
from typing import Dict, Type

PLUGIN_DIR = Path("./plugins")


class PluginManager:
    """Manages the loading and unloading of plugins."""
    
    def __init__(self, plugin_dir: Path = PLUGIN_DIR):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, object] = {}  # name -> instance

    def install_dependencies(self, dependencies: list[str]):
        for dep in dependencies:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

    def load_plugin_from_manifest(self, folder_name: str, manifest: dict):
        entry_point = manifest.get("entry_point")
        if not entry_point:
            raise ValueError("Manifest missing 'entry_point' field")
        
        dependencies = manifest.get("dependencies", [])
        if dependencies:
            self.install_dependencies(dependencies)

        module_name, class_name = entry_point.split(":")
        module_path = f"backend.plugins.{folder_name}.{module_name}"
        
        module = importlib.import_module(module_path)
        cls: Type = getattr(module, class_name)
        
        instance = cls(manifest)
        self.plugins[manifest["name"]] = instance
        return instance

    def get_plugin(self, name: str):
        return self.plugins.get(name)
    
    def get_all_plugins(self):
        return self.plugins

plugin_manager = PluginManager()