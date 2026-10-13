import os
import sys

# Ensure the root project directory is in sys.path so cancer_project can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, '..'))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from cancer_project.app import app

# Vercel Python WSGI handler expects 'app'
# This is the entrypoint executed by Vercel serverless functions
