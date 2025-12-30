from .heuristic import HeuristicDetector
from .base import Detector, DetectionResult

def get_default_detector() -> Detector:
    # Swap here when you add a real ML detector
    return HeuristicDetector()
