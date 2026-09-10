from discovery.domain.errors import require


def next_phase(current: int, target: int | None = None) -> int:
    expected = current + 1
    require(
        1 <= current <= 4 and target in (None, expected),
        "INVALID_TRANSITION",
        "Forward progression must traverse exactly one phase.",
    )
    return expected


def regression_phases(current: int, target: int) -> range:
    require(
        1 <= target < current <= 4, "INVALID_TRANSITION", "Regression must target an earlier phase."
    )
    return range(target, 5)
