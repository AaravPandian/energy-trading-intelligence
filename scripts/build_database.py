"""Run with: python -m scripts.build_database"""
from src.database import build_database

if __name__ == '__main__':
    print(f'SQLite database ready: {build_database()}')
