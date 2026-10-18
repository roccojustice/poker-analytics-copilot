from decimal import Decimal

# suffix -> (name, lo, hi) as fractions of the pot at street start; lo inclusive, hi exclusive
SIZE_BUCKETS = {
    "S": ("small", Decimal("0"), Decimal("0.45")),
    "M": ("medium", Decimal("0.45"), Decimal("0.70")),
    "L": ("large", Decimal("0.70"), Decimal("1.05")),
    "O": ("overbet", Decimal("1.05"), None),
}


def street_bet_sql(street):
    """The street's only bet from Hero's row: Hero's bet, else the bet Hero faced (SCHEMA_NOTES)."""
    return f"(chps.amt_{street}_bet_made + chps.amt_{street}_bet_facing)"


def size_text(size):
    name, lo, hi = SIZE_BUCKETS[size]
    pct = lambda x: f"{int(x * 100)}%"
    if hi is None:
        return f"{name} (≥{pct(lo)})"
    if lo == 0:
        return f"{name} (<{pct(hi)})"
    return f"{name} ({int(lo * 100)}–{pct(hi)})"
