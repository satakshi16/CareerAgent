#!/usr/bin/env python3
"""Convenience entry point:  python generate_resume.py [resume.yaml] [options]"""
import sys
from resume_generator.cli import main

if __name__ == "__main__":
    sys.exit(main())
