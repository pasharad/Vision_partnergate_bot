def rial_to_toman_str(rial: int) -> str:
    toman = rial // 10
    formatted = f"{toman:,}".replace(",", ",")
    return f"{formatted} تومان"


def rial_to_toman_short(rial: int) -> str:
    toman = rial // 10
    if toman >= 1_000_000_000:
        value = toman / 1_000_000_000
        return f"{value:.2f} میلیارد تومان"
    if toman >= 1_000_000:
        value = toman / 1_000_000
        return f"{value:,.0f} میلیون تومان"
    return f"{toman:,} تومان"


def format_area(area: float) -> str:
    return f"{area:,.2f}"


def paginate(items: list, page: int, per_page: int = 10) -> tuple[list, int, bool]:
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    return items[start:end], total_pages, page < total_pages - 1
