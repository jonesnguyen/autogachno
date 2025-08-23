import sys
import os

# Adjust sys.path to include the app directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import main

if __name__ == "__main__":
    main()
