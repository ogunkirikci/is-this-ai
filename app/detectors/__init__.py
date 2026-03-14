from .heuristic import HeuristicDetector
from .itsnotai import ItsNotAIDetector
from .base import Detector, DetectionResult

def get_default_detector() -> Detector:
    return ItsNotAIDetector()
