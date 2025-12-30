from dataclasses import dataclass
from typing import Protocol

@dataclass
class DetectionResult:
    score: float  # 0..1, higher => more likely AI-generated/AI-edited
    confidence: float  # 0..1
    reasons: list[str]

class Detector(Protocol):
    name: str
    def detect_image(self, image_path: str) -> DetectionResult: ...
    def detect_video(self, frames_dir: str) -> DetectionResult: ...
