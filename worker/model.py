"""폐 X-ray 이미지의 폐렴 여부를 예측하는 앙상블 모델.
예측 처리 흐름
1. 업로드 이미지를 회색조로 읽고 CLAHE로 X-ray의 국소 대비를 높인다.
2. 원본 비율을 유지한 채 384 x 384 크기로 letterbox 변환한다.
3. DenseNet121, ConvNeXt-Tiny, EfficientNet-B3의 각 5-fold 모델로 추론한다.
4. 같은 백본의 5개 확률을 평균하고, 설정 파일의 백본별 가중치로 합산한다.
5. 최종 폐렴 확률이 설정 파일의 임계값 이상이면 PNEUMONIA로 판정한다.

모델은 이 모듈이 import될 때 한 번만 메모리에 올라간다. API에서는 업로드된
이미지의 bytes 또는 file 객체를 :func:`predict`에 전달하면 된다.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import BinaryIO

import cv2
import numpy as np
import torch
from PIL import Image, ImageOps, UnidentifiedImageError
from torch import Tensor, nn
from torch.nn import functional as F
from torchvision.models import convnext_tiny, densenet121, efficientnet_b3


MODEL_DIR = Path(__file__).resolve().parent / "models"
CONFIG_PATH = MODEL_DIR / "best_oof_ensemble_config.json"

# 학습 당시 사용한 입력 크기와 ImageNet 사전 학습 backbone의 정규화 값
# 추론 전처리가 학습과 달라지면 예측 성능이 떨어질 수 있으므로 함께 변경해야 한다.
IMAGE_SIZE = 384
IMAGENET_MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
IMAGENET_STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)
MAX_IMAGE_PIXELS = 50_000_000


class ChannelAttention(nn.Module):
    """Feature map에서 진단에 중요한 채널에 더 큰 가중치를 부여"""

    def __init__(self, channels: int, reduction: int = 16) -> None:
        super().__init__()
        hidden_channels = max(channels // reduction, 1)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Conv2d(channels, hidden_channels, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_channels, channels, kernel_size=1, bias=False),
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, inputs: Tensor) -> Tensor:
        # 평균값과 최댓값을 함께 사용해 채널별 중요도를 0~1 사이로 계산한다.
        average = self.fc(self.avg_pool(inputs))
        maximum = self.fc(self.max_pool(inputs))
        return self.sigmoid(average + maximum)


class SpatialAttention(nn.Module):
    """feature map에서 병변과 관련된 공간 위치에 더 큰 가중치를 부여"""

    def __init__(self, kernel_size: int = 7) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(
            2,
            1,
            kernel_size=kernel_size,
            padding=kernel_size // 2,
            bias=False,
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, inputs: Tensor) -> Tensor:
        # 채널 축을 요약한 두 지도를 결합해 위치별 중요도를 계산한다.
        average = torch.mean(inputs, dim=1, keepdim=True)
        maximum, _ = torch.max(inputs, dim=1, keepdim=True)
        return self.sigmoid(self.conv1(torch.cat((average, maximum), dim=1)))


class CBAM(nn.Module):
    """채널 어텐션과 공간 어텐션을 순서대로 적용하는 CBAM 모듈."""
    """
    CBAM(Convolutional Block Attention Module)?
    합성곱 신경망(CNN)의 성능을 높이기 위해 입력된 특징 맵(Feature Map)에 
    채널 어텐션(Channel Attention)과 공간 어텐션(Spatial Attention)을 순차적으로 적용하는 경량 어텐션 모듈
    """

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.ca = ChannelAttention(channels)
        self.sa = SpatialAttention()

    def forward(self, inputs: Tensor) -> Tensor:
        outputs = inputs * self.ca(inputs)
        return outputs * self.sa(outputs)


class PneumoniaClassifier(nn.Module):
    """체크포인트 key 구조(models 파일)에 맞춰 backbone, CBAM, binary classifier를 조립한다."""

    def __init__(self, architecture: str) -> None:
        super().__init__()

        if architecture == "densenet121":
            backbone = densenet121(weights=None)
            # 각 백본의 마지막 feature map 채널 수가 서로 다르다.
            channels = 1024
            # torchvision DenseNet은 pooling 전에 별도로 ReLU를 적용해야 한다.
            self._relu_features = True
        elif architecture == "convnext_tiny":
            backbone = convnext_tiny(weights=None)
            channels = 768
            self._relu_features = False
        elif architecture == "efficientnet_b3":
            backbone = efficientnet_b3(weights=None)
            channels = 1536
            self._relu_features = False
        else:
            raise ValueError(f"지원하지 않는 모델 구조입니다: {architecture}")

        self.features = backbone.features
        self.cbam = CBAM(channels)
        # logit 하나를 출력하며 sigmoid는 앙상블 확률 계산 시 적용한다.
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(channels, 1),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        outputs = self.features(inputs)
        if self._relu_features:
            outputs = F.relu(outputs, inplace=False)
        outputs = self.cbam(outputs)
        outputs = F.adaptive_avg_pool2d(outputs, output_size=1)
        outputs = torch.flatten(outputs, 1)
        return self.classifier(outputs)


def _select_device() -> torch.device:
    """CUDA GPU가 있으면 사용하고, 없으면 CPU에서 추론"""

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _read_config() -> dict:
    """학습 검증으로 정한 백본별 가중치와 최종 판정 임계값을 읽음"""

    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"모델 설정 파일을 찾을 수 없습니다: {CONFIG_PATH}")

    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config.get("best_weights"), dict):
        raise ValueError("모델 설정에 best_weights가 없습니다.")
    if "best_threshold" not in config:
        raise ValueError("모델 설정에 best_threshold가 없습니다.")
    return config


class PneumoniaEnsemble(nn.Module):
    """설정 파일의 모델 가중치와 threshold를 적용한 5-fold 앙상블"""

    def __init__(self, device: torch.device | None = None) -> None:
        super().__init__()
        config = _read_config()
        self.device = device or _select_device()

        # 0.36과 0.75/0.15/0.10은 임의의 상수가 아니라 OOF 검증으로 선택된
        # best_threshold와 best_weights이며 설정 파일을 단일 기준으로 함.
        self.threshold = float(config["best_threshold"])
        self.model_name = str(config.get("experiment", "pneumonia_ensemble"))
        self.architecture_weights = {
            name: float(weight) for name, weight in config["best_weights"].items()
        }
        self.models = nn.ModuleDict()

        weight_sum = sum(self.architecture_weights.values())
        if weight_sum <= 0:
            raise ValueError("앙상블 모델 가중치의 합은 0보다 커야 합니다.")
        self.architecture_weights = {
            name: weight / weight_sum
            for name, weight in self.architecture_weights.items()
        }

        # 백본마다 fold0~fold4 체크포인트를 모두 메모리에 올린다. 요청마다
        # 체크포인트를 다시 읽지 않아 반복 예측 시 디스크 I/O가 발생하지 않는다.
        for architecture in self.architecture_weights:
            checkpoint_paths = sorted(
                MODEL_DIR.glob(f"best_{architecture}_384_fold*.pt")
            )
            if not checkpoint_paths:
                raise FileNotFoundError(
                    f"{architecture} 체크포인트를 찾을 수 없습니다: {MODEL_DIR}"
                )

            fold_models = nn.ModuleList()
            for checkpoint_path in checkpoint_paths:
                fold_model = PneumoniaClassifier(architecture)
                state_dict = torch.load(
                    checkpoint_path,
                    map_location=self.device,
                    weights_only=True,
                )
                # strict=True로 학습 모델과 현재 코드의 레이어 구성이 같은지 검증한다.
                fold_model.load_state_dict(state_dict, strict=True)
                fold_model.to(self.device)
                fold_model.eval()
                fold_models.append(fold_model)
                del state_dict

            self.models[architecture] = fold_models

        self.eval()

    @torch.inference_mode()
    def pneumonia_probability(self, image_tensor: Tensor) -> float:
        image_tensor = image_tensor.to(self.device)
        ensemble_probability = torch.zeros((), device=self.device)

        for architecture, fold_models in self.models.items():
            # 각 모델의 logit을 sigmoid로 변환하면 0~1 사이 폐렴 확률 출력
            fold_probabilities = [
                torch.sigmoid(fold_model(image_tensor)).squeeze()
                for fold_model in fold_models
            ]
            # 먼저 같은 백본의 5-fold 결과를 평균해 fold별 편차를 줄임
            architecture_probability = torch.stack(fold_probabilities).mean()
            # 그다음 설정 파일에서 정한 백본별 가중치를 곱해 최종 확률에 더함
            ensemble_probability += (
                architecture_probability * self.architecture_weights[architecture]
            )

        return float(ensemble_probability.detach().cpu().item())


ImageInput = str | Path | bytes | bytearray | memoryview | BinaryIO | Image.Image


def _open_image(image: ImageInput) -> Image.Image:
    """업로드 이미지의 여러 표현을 독립된 회색조 PIL 이미지로 변환"""

    try:
        if isinstance(image, Image.Image):
            opened_image = image
        elif isinstance(image, (str, Path)):
            opened_image = Image.open(image)
        elif isinstance(image, (bytes, bytearray, memoryview)):
            opened_image = Image.open(io.BytesIO(bytes(image)))
        else:
            upload_stream = getattr(image, "file", image)
            if not hasattr(upload_stream, "read"):
                raise TypeError(
                    "image는 경로, bytes, PIL 이미지 또는 binary file 객체여야 합니다."
                )
            opened_image = Image.open(upload_stream)

        opened_image.load()
        if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
            raise ValueError("업로드 이미지의 해상도가 너무 큽니다.")

        # EXIF 회전 정보를 반영하고 X-ray 전처리를 위해 단일 채널로 통일한다.
        return ImageOps.exif_transpose(opened_image).convert("L").copy()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("올바른 이미지 파일이 아닙니다.") from exc


def _letterbox(image: np.ndarray, size: int) -> np.ndarray:
    """이미지를 왜곡하지 않고 비율을 유지하며 정사각형 캔버스에 배치"""

    height, width = image.shape
    if height <= 0 or width <= 0:
        raise ValueError("업로드 이미지의 크기가 올바르지 않습니다.")

    scale = min(size / width, size / height)
    resized_width = max(1, round(width * scale))
    resized_height = max(1, round(height * scale))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(
        image,
        (resized_width, resized_height),
        interpolation=interpolation,
    )

    # 남는 영역은 검은색으로 채우고 리사이즈한 영상을 중앙에 배치한다.
    canvas = np.zeros((size, size), dtype=np.uint8)
    x_offset = (size - resized_width) // 2
    y_offset = (size - resized_height) // 2
    canvas[
        y_offset : y_offset + resized_height,
        x_offset : x_offset + resized_width,
    ] = resized
    return canvas


def preprocess_image(image: ImageInput) -> Tensor:
    """학습 때 사용한 CLAHE, letterbox 및 ImageNet 정규화를 적용"""

    grayscale = np.asarray(_open_image(image), dtype=np.uint8)

    # CLAHE는 X-ray 전체 밝기를 과도하게 바꾸지 않으면서 폐 영역의 국소 대비를
    # 높여 흐릿한 음영과 병변 특징을 모델이 구분하기 쉽게 만듬.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(grayscale)
    letterboxed = _letterbox(enhanced, IMAGE_SIZE)

    # 사전 학습 백본이 3채널 입력을 기대하므로 동일한 회색조 채널을 3번 복제한다.
    rgb_image = np.repeat(letterboxed[:, :, np.newaxis], repeats=3, axis=2)

    # [H, W, C] 이미지를 정규화한 뒤 PyTorch 형식 [N, C, H, W]로 변환한다.
    normalized = rgb_image.astype(np.float32) / 255.0
    normalized = (normalized - IMAGENET_MEAN) / IMAGENET_STD
    channel_first = np.ascontiguousarray(normalized.transpose(2, 0, 1))
    return torch.from_numpy(channel_first).unsqueeze(0)


# 모듈 import 시 한 번만 로드하고 이후 요청에서는 같은 모델을 재사용
model = PneumoniaEnsemble()


def predict(image: ImageInput) -> dict[str, bool | float | str]:
    """
    업로드된 X-ray 이미지의 폐렴 예측 결과를 반환
    confidence와 pneumonia_probability는 DB의 Numeric(5, 2) 컬럼에 바로
    저장할 수 있도록 0~100 사이의 백분율로 반환.
    """

    probability = model.pneumonia_probability(preprocess_image(image))

    # pneumonia_probability는 폐렴 자체의 확률 
    # confidence는 최종으로 선택된 클래스에 대한 신뢰도(확신도)이므로 정상 판정일 때는 (1 - 확률)을 사용
    is_pneumonia = probability >= model.threshold
    confidence = probability if is_pneumonia else 1.0 - probability

    return {
        "prediction": "PNEUMONIA" if is_pneumonia else "NORMAL",
        "is_pneumonia": is_pneumonia,
        "confidence": round(confidence * 100.0, 2),
        "pneumonia_probability": round(probability * 100.0, 2),
        "threshold": round(model.threshold * 100.0, 2),
        "ai_model": model.model_name,
    }


predict_pneumonia = predict
