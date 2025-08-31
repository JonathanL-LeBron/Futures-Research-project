from dataclasses import dataclass, field
from typing import Dict, Set
from sortedcontainers import SortedDict

@dataclass
class LevelData:
    total_size: int = 0
    order_count: int = 0
    order_ids: Set[str] = field(default_factory=set)

@dataclass
class OrderData:
    side: str
    price: float
    size: int

@dataclass
class BookStats:
    total_size: int = 0
    total_count: int = 0

class OrderBook:
    def __init__(self):
        # PER-INSTANCE state — create here, not at class level
        self.bids = SortedDict()          # price -> LevelData (bids)
        self.asks = SortedDict()          # price -> LevelData (asks)
        self.orders: Dict[str, OrderData] = {}
        self.bid_stats = BookStats()
        self.ask_stats = BookStats()

    # --- handlers (snake_case) ---
    def add_order(self, order_id: str, side: str, price: float, size: int) -> None:
        book_side = self.bids if side == 'B' else self.asks
        level = book_side.setdefault(price, LevelData())
        level.total_size += size
        level.order_count += 1
        level.order_ids.add(order_id)

        stats = self.bid_stats if side == 'B' else self.ask_stats
        stats.total_size += size
        stats.total_count += 1

        self.orders[order_id] = OrderData(side=side, price=price, size=size)

    def cancel_order(self, order_id: str) -> None:
        data = self.orders.get(order_id)
        if not data:
            return
        book_side = self.bids if data.side == 'B' else self.asks
        level = book_side[data.price]
        level.total_size -= data.size
        level.order_count -= 1
        level.order_ids.discard(order_id)

        stats = self.bid_stats if data.side == 'B' else self.ask_stats
        stats.total_size -= data.size
        stats.total_count -= 1

        if level.order_count == 0:
            del book_side[data.price]
        del self.orders[order_id]

    def modify_order(self, order_id: str, new_size: int) -> None:
        data = self.orders.get(order_id)
        if not data or new_size < 0:
            return
        delta = new_size - data.size
        if delta == 0:
            return
        book_side = self.bids if data.side == 'B' else self.asks
        level = book_side[data.price]
        level.total_size += delta

        stats = self.bid_stats if data.side == 'B' else self.ask_stats
        stats.total_size += delta

        data.size = new_size
        self.orders[order_id] = data

    def fill_order(self, order_id: str, fill_size: int) -> None:
        data = self.orders.get(order_id)
        if not data or fill_size <= 0:
            return
        remaining = data.size - fill_size
        book_side = self.bids if data.side == 'B' else self.asks
        level = book_side[data.price]
        stats = self.bid_stats if data.side == 'B' else self.ask_stats

        if remaining > 0:
            level.total_size -= fill_size
            stats.total_size -= fill_size
            data.size = remaining
            self.orders[order_id] = data
        else:
            # full or over-fill
            level.total_size -= data.size
            level.order_count -= 1
            stats.total_size -= data.size
            stats.total_count -= 1
            level.order_ids.discard(order_id)
            del self.orders[order_id]
            if level.order_count == 0:
                del book_side[data.price]