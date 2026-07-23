# 폐렴 앙상블 모델 평가 보고서

## 평가 방식

- 평가 유형: 5-fold OOF 검증
- 모델: strict_focal_clahe_letterbox_384_5fold
- Threshold: 0.36
- 평가 표본 수: 5,216개
- 독립 테스트 결과가 아닌 OOF 내부 검증 결과임

## 앙상블 가중치

| Backbone | Weight |
|---|---:|
| DenseNet121 | 0.75 |
| ConvNeXt-Tiny | 0.15 |
| EfficientNet-B3 | 0.10 |

## Confusion Matrix

| 실제 / 예측 | 정상 | 폐렴 |
|---|---:|---:|
| 정상 | TN 1,322 | FP 19 |
| 폐렴 | FN 17 | TP 3,858 |

## 평가 결과

| 지표 | 결과 | 최소 기준 | 판정 |
|---|---:|---:|---|
| Recall | 0.9956 | 0.90 | PASS |
| Accuracy | 0.9931 | 0.80 | PASS |
| F1-score | 0.9954 | 보조 지표 | PASS |
| AUROC | 0.9995 | 보조 지표 | PASS |

## 계산식

Recall:

```text
3858 / (3858 + 17) = 0.9956
```
Accuracy:

```text
(3858 + 1322) / 5216 = 0.9931
```

## 자동 검증

저장된 OOF 설정의 혼동행렬과 프로젝트 통과 기준은 다음 명령으로 다시
계산할 수 있다.

```bash
uv run python -m worker.models.model_1.evaluate
```

JSON 결과가 필요하면 다음 옵션을 사용한다.

```bash
uv run python -m worker.models.model_1.evaluate --json
```

스크립트는 Recall과 Accuracy가 모두 기준을 충족하면 종료 코드 `0`, 하나라도
충족하지 못하면 `1`, 평가 데이터가 올바르지 않으면 `2`를 반환한다.

## 결론

폐렴 Recall과 Accuracy 모두 프로젝트 최소 기준을 충족한다.

단, 본 결과는 독립 테스트셋이 아닌 OOF 검증 결과이므로 실제 임상 성능을
의미하지 않는다. Grad-CAM 역시 모델의 관심 영역을 표시할 뿐 병변 위치를
확정하는 진단 결과가 아니다.
