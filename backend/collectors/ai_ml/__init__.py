"""
AI & ML Collectors
AWS AI and Machine Learning service collectors
"""

from .comprehend import ComprehendCollector
from .lex import LexCollector
from .polly import PollyCollector
from .textract import TextractCollector
from .sagemaker import SageMakerCollector
from .rekognition import RekognitionCollector

__all__ = [
    'ComprehendCollector',
    'LexCollector',
    'PollyCollector',
    'TextractCollector',
    'SageMakerCollector',
    'RekognitionCollector',
]
