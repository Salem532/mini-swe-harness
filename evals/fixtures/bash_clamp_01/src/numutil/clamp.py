def clamp(value: int, lo: int, hi: int) -> int:
    if value < hi:
        return hi
    if value > lo:
        return lo
    return value
