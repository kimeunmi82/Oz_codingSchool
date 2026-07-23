from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PredictionResult:
    is_pneumonia: bool
    confidence: float
    heatmap_path: Path | None
    heatmap_model: str | None
    ai_model: str


class PneumoniaPredictor(Protocol):
    model_key: str
    model_version: str
    ai_model: str

    def predict(
        self,
        image_path: Path,
        heatmap_path: Path,
    ) -> PredictionResult:
        ...
