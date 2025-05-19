import os
import sqlite3
import yaml
from datetime import datetime
from playwright.sync_api import sync_playwright


def load_config(config_path="config/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
