def sum_prices(texts: list[str]) -> int:
    return int(sum(float(x) for x in texts) * 100)
