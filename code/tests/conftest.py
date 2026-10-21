import sys
import os

# code/ 디렉토리를 Python 경로에 추가 (pytest 어디서 실행하든 동작)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
