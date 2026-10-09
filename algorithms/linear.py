"""Small, dependency-free baselines; all fitting uses supplied training rows only."""

import math
from collections.abc import Mapping
from numbers import Real


def _finite_float(value, label):
    """Convert a real scalar to float and reject booleans and non-finite values."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite real number")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite real number")
    return result


def _scaled_mean(values):
    """Compute a mean without overflowing the intermediate sum."""
    scale = max(abs(value) for value in values)
    if scale == 0.0:
        return 0.0
    result = (math.fsum(value / scale for value in values) / len(values)) * scale
    if not math.isfinite(result):
        raise ValueError("mean is outside the finite float range")
    return result


def _scaled_ratio(factor, numerator, denominator, label):
    """Compute factor * numerator / denominator with exponent-aware scaling."""
    if factor == 0.0 or numerator == 0.0:
        return 0.0
    factor_mantissa, factor_exponent = math.frexp(factor)
    numerator_mantissa, numerator_exponent = math.frexp(numerator)
    denominator_mantissa, denominator_exponent = math.frexp(denominator)
    mantissa = factor_mantissa * numerator_mantissa / denominator_mantissa
    exponent = factor_exponent + numerator_exponent - denominator_exponent
    try:
        result = math.ldexp(mantissa, exponent)
    except OverflowError as exc:
        raise ValueError(f"{label} is outside the finite float range") from exc
    if not math.isfinite(result) or result == 0.0:
        raise ValueError(f"{label} is outside the finite float range")
    return result


def check_rows(rows):
    """Validate and normalize two-column observations."""
    try:
        raw_rows = list(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of two finite numbers") from exc
    if len(raw_rows) < 2:
        raise ValueError("at least two observations required")

    normalized = []
    for row_index, row in enumerate(raw_rows):
        if isinstance(row, (str, bytes)):
            raise ValueError("rows must contain two finite numbers")
        try:
            values = list(row)
        except TypeError as exc:
            raise ValueError("rows must contain two finite numbers") from exc
        if len(values) != 2:
            raise ValueError("rows must contain two finite numbers")
        normalized.append(
            (
                _finite_float(values[0], f"row {row_index} x"),
                _finite_float(values[1], f"row {row_index} y"),
            )
        )
    return normalized


def fit(rows, model):
    normalized = check_rows(rows)
    xs, ys = zip(*normalized)
    if model == "mean":
        return {"intercept": _scaled_mean(ys), "slope": 0.0}
    if model == "last":
        return {"intercept": ys[-1], "slope": 0.0}
    if model != "linear":
        raise ValueError("unknown model")

    x_scale = max(abs(value) for value in xs)
    if x_scale == 0.0:
        raise ValueError("singular time column")
    scaled_xs = [value / x_scale for value in xs]
    scaled_x_mean = math.fsum(scaled_xs) / len(scaled_xs)
    centered_xs = [value - scaled_x_mean for value in scaled_xs]
    denominator = math.fsum(value * value for value in centered_xs)
    if denominator == 0.0 or not math.isfinite(denominator):
        raise ValueError("numerically singular time column")

    y_scale = max(abs(value) for value in ys)
    if y_scale == 0.0:
        return {"intercept": 0.0, "slope": 0.0}
    scaled_ys = [value / y_scale for value in ys]
    scaled_y_mean = math.fsum(scaled_ys) / len(scaled_ys)
    centered_ys = [value - scaled_y_mean for value in scaled_ys]
    covariance = math.fsum(
        x_value * y_value for x_value, y_value in zip(centered_xs, centered_ys)
    )
    scaled_slope = covariance / denominator
    if not math.isfinite(scaled_slope):
        raise ValueError("slope is outside the finite float range")
    slope = _scaled_ratio(scaled_slope, y_scale, x_scale, "slope")

    x_mean = _scaled_mean(xs)
    y_mean = _scaled_mean(ys)
    intercept = y_mean - slope * x_mean
    if not math.isfinite(intercept):
        raise ValueError("intercept is outside the finite float range")
    return {"intercept": intercept, "slope": slope}


def predict(parameters, xs):
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must contain finite intercept and slope values")
    try:
        intercept = _finite_float(parameters["intercept"], "intercept")
        slope = _finite_float(parameters["slope"], "slope")
    except KeyError as exc:
        raise ValueError("parameters must contain finite intercept and slope values") from exc
    try:
        normalized_xs = [_finite_float(value, "prediction x") for value in xs]
    except TypeError as exc:
        raise ValueError("prediction inputs must be an iterable of finite real numbers") from exc

    result = []
    for value in normalized_xs:
        prediction = intercept + slope * value
        if not math.isfinite(prediction):
            raise ValueError("prediction is outside the finite float range")
        result.append(prediction)
    return result


def metrics(actual, predicted):
    try:
        actual_values = list(actual)
        predicted_values = list(predicted)
    except TypeError as exc:
        raise ValueError("metric vectors must be finite numeric iterables") from exc
    if not actual_values or len(actual_values) != len(predicted_values):
        raise ValueError("empty or mismatched metric vectors")

    normalized_actual = [
        _finite_float(value, "actual metric value") for value in actual_values
    ]
    normalized_predicted = [
        _finite_float(value, "predicted metric value") for value in predicted_values
    ]
    errors = []
    for actual_value, predicted_value in zip(normalized_actual, normalized_predicted):
        error = actual_value - predicted_value
        if not math.isfinite(error):
            raise ValueError("metric error is outside the finite float range")
        errors.append(error)

    scale = max(abs(error) for error in errors)
    if scale == 0.0:
        return {"mae": 0.0, "rmse": 0.0}
    scaled_absolute_errors = [abs(error) / scale for error in errors]
    mae = scale * (math.fsum(scaled_absolute_errors) / len(errors))
    rmse = scale * math.sqrt(
        math.fsum(value * value for value in scaled_absolute_errors) / len(errors)
    )
    if not math.isfinite(mae) or not math.isfinite(rmse):
        raise ValueError("metrics are outside the finite float range")
    return {"mae": mae, "rmse": rmse}
