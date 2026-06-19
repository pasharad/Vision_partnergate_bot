from dataclasses import dataclass
from datetime import datetime


@dataclass
class Board:
    board_code: str
    station: str
    status: str
    reservation_end: str
    city: str
    description: str
    mode: str
    price_monthly: int
    price_2month: int
    price_3_5month: int
    price_6_8month: int
    area_sqm: float
    print_unit_price: int
    print_total_cost: int


class DataCache:
    def __init__(self):
        self.boards: list[Board] = []
        self.last_loaded: datetime | None = None

    @property
    def is_stale(self) -> bool:
        if self.last_loaded is None:
            return True
        from datetime import timedelta
        import config
        return datetime.now() - self.last_loaded > timedelta(hours=config.RELOAD_INTERVAL_HOURS)

    def get_available(self) -> list[Board]:
        return [b for b in self.boards if b.status == "خالی"]

    def get_occupied(self) -> list[Board]:
        return [b for b in self.boards if b.status == "پر"]

    def get_by_code(self, code: str) -> Board | None:
        for b in self.boards:
            if b.board_code == code:
                return b
        return None

    def search(self, query: str) -> list[Board]:
        q = query.lower()
        return [
            b for b in self.boards
            if q in b.board_code.lower()
            or q in b.station.lower()
            or q in b.city.lower()
            or q in b.description.lower()
        ]
