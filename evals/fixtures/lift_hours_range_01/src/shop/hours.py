def is_open(weekday: int, hour: int) -> bool:
    return 9 <= (hour % 24) <= 17
