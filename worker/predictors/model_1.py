from pathlib import Path

from worker.predictors.base import PredictionResult


class Model1Predictor:
    """기존 5-fold weighted ensemble 모델 어댑터."""

    model_key = "model_1"
    experiment_name = "strict_focal_clahe_letterbox_384_5fold"
    model_version = "1.0.0"
    ai_model = experiment_name

    def predict(
        self,
        image_path: Path,
        heatmap_path: Path,
    ) -> PredictionResult:
        # 무거운 체크포인트는 model_1 예측이 실제 요청될 때만 로드한다.
        from worker.models.model_1.model import predict_with_gradcam

        result = predict_with_gradcam(image_path, heatmap_path)

        return PredictionResult(
            is_pneumonia=bool(result["is_pneumonia"]),
            confidence=float(result["confidence"]),
            heatmap_path=heatmap_path,
            heatmap_model=str(result["heatmap_model"]),
            ai_model=self.ai_model,
        )
