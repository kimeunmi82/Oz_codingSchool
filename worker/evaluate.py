"""폐렴 앙상블 모델의 저장된 OOF 성능 결과를 자동 검증한다.

중요:
- 이 스크립트는 새로 입력된 X-ray 이미지를 예측하거나 평가하지 않는다.
- 학습 과정에서 저장한 ``best_oof_ensemble_config.json``의 혼동행렬을 읽는다.
- 혼동행렬로 Recall과 Accuracy를 다시 계산하고 프로젝트 기준의 PASS/FAIL
  여부를 확인한다.
- 실제 이미지 기반 성능 평가는 정답 라벨이 있는 별도의 테스트 데이터셋이
  있어야 수행할 수 있다.

용도:
- 평가 계산 방식 통일
- 수기 계산 오류 방지
- 모델 설정 변경 시 최소 성능 기준 확인
- PR 또는 CI에서 성능 기준 자동 검증
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "best_oof_ensemble_config.json"
)
DEFAULT_MIN_RECALL = 0.90
DEFAULT_MIN_ACCURACY = 0.80


class EvaluationDataError(ValueError):
    """평가 설정의 필수 데이터가 없거나 올바르지 않은 경우."""


def _nonnegative_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvaluationDataError(
            f"{name}은 0 이상의 정수여야 합니다."
        )
    return value


def _ratio(numerator: int, denominator: int, metric_name: str) -> float:
    if denominator == 0:
        raise EvaluationDataError(
            f"{metric_name}을 계산할 수 없습니다: 분모가 0입니다."
        )
    return numerator / denominator


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        raise EvaluationDataError(
            f"평가 설정 파일을 찾을 수 없습니다: {config_path}"
        )

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationDataError(
            f"평가 설정 파일을 읽을 수 없습니다: {config_path}"
        ) from exc

    if not isinstance(config, dict):
        raise EvaluationDataError("평가 설정의 최상위 값은 객체여야 합니다.")
    return config


def evaluate_oof(
    config: dict[str, Any],
    min_recall: float = DEFAULT_MIN_RECALL,
    min_accuracy: float = DEFAULT_MIN_ACCURACY,
) -> dict[str, Any]:
    """저장된 OOF 혼동행렬로 지표와 평가 기준 통과 여부를 계산한다.

    실제 X-ray 추론을 실행하지 않으며 독립 테스트셋 평가를 대체하지 않는다.
    """

    for criterion_name, criterion_value in (
        ("min_recall", min_recall),
        ("min_accuracy", min_accuracy),
    ):
        if not math.isfinite(criterion_value) or not 0 <= criterion_value <= 1:
            raise EvaluationDataError(
                f"{criterion_name}은 0과 1 사이여야 합니다."
            )

    confusion_matrix = config.get("confusion_matrix")
    if (
        not isinstance(confusion_matrix, list)
        or len(confusion_matrix) != 2
        or any(
            not isinstance(row, list) or len(row) != 2
            for row in confusion_matrix
        )
    ):
        raise EvaluationDataError(
            "confusion_matrix는 [[TN, FP], [FN, TP]] 형식이어야 합니다."
        )

    tn = _nonnegative_integer(confusion_matrix[0][0], "TN")
    fp = _nonnegative_integer(confusion_matrix[0][1], "FP")
    fn = _nonnegative_integer(confusion_matrix[1][0], "FN")
    tp = _nonnegative_integer(confusion_matrix[1][1], "TP")
    total = tn + fp + fn + tp
    if total == 0:
        raise EvaluationDataError("평가 표본 수가 0입니다.")

    recall = _ratio(tp, tp + fn, "Recall")
    accuracy = _ratio(tp + tn, total, "Accuracy")
    precision = _ratio(tp, tp + fp, "Precision")
    specificity = _ratio(tn, tn + fp, "Specificity")
    f1_score = _ratio(
        2 * precision * recall,
        precision + recall,
        "F1-score",
    )

    recall_passed = recall >= min_recall
    accuracy_passed = accuracy >= min_accuracy
    passed = recall_passed and accuracy_passed

    return {
        "evaluation_type": "5-fold OOF",
        "model_name": config.get("experiment", "unknown"),
        "threshold": config.get("best_threshold"),
        "architecture_weights": config.get("best_weights", {}),
        "sample_count": total,
        "class_distribution": {
            "normal": tn + fp,
            "pneumonia": tp + fn,
        },
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
        "metrics": {
            "recall": recall,
            "accuracy": accuracy,
            "precision": precision,
            "specificity": specificity,
            "f1_score": f1_score,
            "auroc": config.get("oof_auroc"),
        },
        "criteria": {
            "min_recall": min_recall,
            "min_accuracy": min_accuracy,
            "recall_passed": recall_passed,
            "accuracy_passed": accuracy_passed,
        },
        "passed": passed,
        "limitations": (
            "독립 테스트셋이 아닌 5-fold OOF 내부 검증 결과입니다."
        ),
    }


def _format_percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def _print_text_report(result: dict[str, Any]) -> None:
    confusion = result["confusion_matrix"]
    metrics = result["metrics"]
    criteria = result["criteria"]

    print("폐렴 앙상블 모델 OOF 평가")
    print(f"모델: {result['model_name']}")
    print(f"Threshold: {result['threshold']}")
    print(f"표본 수: {result['sample_count']}")
    print(
        "Confusion Matrix: "
        f"TN={confusion['tn']}, FP={confusion['fp']}, "
        f"FN={confusion['fn']}, TP={confusion['tp']}"
    )
    print(
        f"Recall: {_format_percentage(metrics['recall'])} "
        f"(기준 {_format_percentage(criteria['min_recall'])}) "
        f"{'PASS' if criteria['recall_passed'] else 'FAIL'}"
    )
    print(
        f"Accuracy: {_format_percentage(metrics['accuracy'])} "
        f"(기준 {_format_percentage(criteria['min_accuracy'])}) "
        f"{'PASS' if criteria['accuracy_passed'] else 'FAIL'}"
    )
    print(f"F1-score: {_format_percentage(metrics['f1_score'])}")
    print(f"최종 판정: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"주의: {result['limitations']}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="폐렴 앙상블 모델의 저장된 OOF 평가 결과를 검증합니다.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="OOF 앙상블 설정 JSON 경로",
    )
    parser.add_argument(
        "--min-recall",
        type=float,
        default=DEFAULT_MIN_RECALL,
        help="필수 Recall 기준(기본값: 0.90)",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=DEFAULT_MIN_ACCURACY,
        help="필수 Accuracy 기준(기본값: 0.80)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="결과를 JSON 형식으로 출력",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        config = _load_config(args.config)
        result = evaluate_oof(
            config,
            min_recall=args.min_recall,
            min_accuracy=args.min_accuracy,
        )
    except EvaluationDataError as exc:
        print(f"평가 실패: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text_report(result)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
