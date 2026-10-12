import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, '..')
sys.path.insert(0, project_dir)

from cancer_project.app import app
