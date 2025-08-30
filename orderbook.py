from dataclasses import dataclass, field
from typing import Dict, Set
from sortedcontainers import SortedDict
@dataclass
class LevelData:
    total_size: int = 0                # sum of sizes at this price
    order_count: int = 0               # number of active orders here
    order_ids: Set[str] = field(default_factory=set)

@dataclass
class OrderData:
    side: str                          # 'B' for bid, 'A' for ask
    price: float                       # order price
    size: int                          # remaining order size

class BookStats:
    total_size: int = 0
    total_count: int = 0

class OrderBook:
    def __init__(self):
        # price -> LevelData, bids descending, asks ascending
        self.bids: SortedDict[float, LevelData] = SortedDict(lambda x: -x)
        self.asks: SortedDict[float, LevelData] = SortedDict()
        self.orders: Dict[str, OrderData] = {}
        self.bid_stats: BookStats = field(default_factory=BookStats)
        self.ask_stats: BookStats = field(default_factory=BookStats)

    def add_order(self, order_id: str, side: str, price: float, size: int) -> None:
        book_side = self.bids if side == 'B' else self.asks
        # ensure level exists
        if price not in book_side:
            book_side[price] = LevelData(total_size=0, order_count = 0, order_ids = set())
        level = book_side[price]
        # update aggregates
        level.total_size += size
        level.order_count += 1
        stats = self.bid_stats if side == 'B' else self.ask_stats
        stats.total_size += size
        stats.total_count += 1

        level.order_ids.add(order_id)
        # record order
        self.orders[order_id] = OrderData(side=side, price=price, size=size)

    def cancel_order(self, order_id: str) -> None:
        if order_id not in self.orders:
            return
        data = self.orders.pop(order_id)
        book_side = self.bids if data.side == 'B' else self.asks
        level = book_side[data.price]
        # decrement aggregates
        level.total_size -= data.size
        level.order_count -= 1
        stats = self.bid_stats if data.side == 'B' else self.ask_stats
        stats.total_size -= data.size
        stats.total_count -= 1
        level.order_ids.remove(order_id)
        # remove empty level
        if level.order_count == 0:
            del book_side[data.price]

    def modify_order(self, order_id: str, new_size: int) -> None:
        if order_id not in self.orders:
            return
        data = self.orders[order_id]
        size_delta = new_size - data.size
        book_side = self.bids if data.side == 'B' else self.asks
        level = book_side[data.price]
        # adjust aggregates
        level.total_size += size_delta
        stats = self.bid_stats if data.side == 'B' else ask_stats
        stats.total_size += size_delta
        # update order record
        data.size = new_size
        self.orders[order_id] = data

    def fill_order(self, order_id: str, fill_size: int) -> None:
        if order_id not in self.orders:
            return
        data = self.orders[order_id]
        remaining = data.size - fill_size
        book_side = self.bids if data.side == 'B' else self.asks
        level = book_side[data.price]
        if remaining > 0:
            # partial fill
            level.total_size -= fill_size
            stats = self.bid_stats if data.side == 'B' else self.ask_stats
            stats.total_size -= fill_size
            data.size = remaining
            self.orders[order_id] = data
        else:
            # full or over-fill
            level.total_size -= data.size
            level.order_count -= 1
            stats = self.bid_stats if data.side == 'B' else self.ask_stats
            stats.total_size -= data.size
            stats.total_count -= 1
            level.order_ids.remove(order_id)
            del self.orders[order_id]
            # clean up level
            if level.order_count == 0:
                del book_side[data.price]
