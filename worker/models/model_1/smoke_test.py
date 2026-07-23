"""앙상블 모델 설치와 전체 추론 경로를 빠르게 확인하는 스모크 테스트.

실행 방법:
    uv run python -m worker.models.model_1.smoke_test
    uv run python -m worker.models.model_1.smoke_test path/to/xray.jpg

이미지를 생략하면 의학적 의미가 없는 임시 회색조 이미지로 코드 실행 여부만
확인한다. 실제 모델 품질 검증에는 정상/폐렴 X-ray 이미지를 각각 사용해야 한다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from worker.models.model_1.model import model, predict


EXPECTED_MODEL_COUNT = 15


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="폐렴 앙상블 모델 스모크 테스트")
    parser.add_argument(
        "image",
        nargs="?",
        type=Path,
        help="선택 사항: 예측할 X-ray 이미지 경로",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    loaded_model_count = sum(
        len(fold_models) for fold_models in model.models.values()
    )
    if loaded_model_count != EXPECTED_MODEL_COUNT:
        raise RuntimeError(
            f"모델 수가 올바르지 않습니다: "
            f"expected={EXPECTED_MODEL_COUNT}, actual={loaded_model_count}"
        )

    if args.image is not None:
        if not args.image.is_file():
            raise FileNotFoundError(f"테스트 이미지를 찾을 수 없습니다: {args.image}")
        test_image = args.image
        image_description = str(args.image)
    else:
        # 모델 연결 상태만 검사하기 위한 임시 입력이며 결과에 의학적 의미는 없다.
        test_image = Image.new("L", (512, 384), color=128)
        image_description = "synthetic grayscale image"

    result = predict(test_image)

    print("Pneumonia ensemble smoke test: PASS")
    print(f"device: {model.device}")
    print(f"loaded models: {loaded_model_count}")
    print(f"threshold: {model.threshold}")
    print(f"weights: {model.architecture_weights}")
    print(f"input: {image_description}")
    print("result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
