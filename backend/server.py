"""
NT Commerce API Server - Legacy Entry Point
Delegates to main.py which contains the actual application.
This file exists only for supervisor compatibility.
"""
from main import app
