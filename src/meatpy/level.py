"""Limit order book level management.

This module provides classes for managing individual price levels in a limit
order book, including order queues, execution logic, and CSV export functionality.
"""

from typing import Any, Generic

from meatpy.timestamp import Timestamp

from .types import OrderID, Price, Qualifiers, Volume


class ExecutionPriorityException(Exception):
    """Exception raised when market priority (price/time preference) is not respected.

    This exception is raised when an order execution violates the priority
    rules of the limit order book, such as executing an order that is not
    first in the queue.
    """

    pass


class VolumeInconsistencyException(Exception):
    """Exception raised when the volume of a trade or cancel is larger than the volume on the book.

    This exception is raised when attempting to execute or cancel a volume
    that exceeds the available volume at a price level.
    """

    pass


class OrderNotFoundError(Exception):
    """Exception raised when an order is not found in the limit order book.

    This exception is raised when attempting to perform operations on an order
    that does not exist in the specified price level or queue.
    """

    pass


class OrderOnBook(Generic[Volume, OrderID, Qualifiers]):
    """An order currently on the book.

    This is a low-level order structure for orders on the book. The order
    type and price are irrelevant here, they depend on the queue and
    level the order belongs to.

    Attributes:
        order_id: Unique identifier for the order
        timestamp: When the order was placed
        volume: Remaining volume of the order
        qualifs: Optional qualifiers for the order
    """

    def __init__(
        self,
        order_id: OrderID,
        timestamp: Timestamp,
        volume: Volume,
        qualifs: Qualifiers | None = None,
    ) -> None:
        self.order_id: OrderID = order_id
        self.timestamp: Timestamp = timestamp
        self.volume: Volume = volume
        self.qualifs: Qualifiers | None = qualifs

    def print_out(self, indent: str = "") -> None:
        """Print order information as a log.

        Args:
            indent: Indentation string for formatting
        """
        print(
            f"{indent}{self.volume} shares entered at {self.timestamp} (id {self.order_id})"
        )

    def get_order_data(self) -> dict[str, Any]:
        """Get structured data for this order.

        Returns:
            Dictionary containing order data
        """
        return {
            "order_id": self.order_id,
            "timestamp": self.timestamp,
            "volume": self.volume,
            "qualifs": self.qualifs,
        }

    def to_record(
        self,
        order_type_str: str,
        level_num: int,
        price: Price,
        timestamp: Timestamp,
        show_age: bool = False,
    ) -> dict[str, Any]:
        """Convert order to a structured record.

        This method provides direct access to order data without the
        overhead of CSV serialization and parsing.

        Args:
            order_type_str: Type of order (e.g., 'Ask', 'Bid')
            level_num: Price level number
            price: Price of the level
            timestamp: Current timestamp for the record
            show_age: Whether to include age information

        Returns:
            Dictionary record representing the order
        """
        if show_age:
            age = timestamp - self.timestamp
            return {
                "Timestamp": str(timestamp),
                "Type": order_type_str,
                "Level": level_num,
                "Price": float(price),
                "Order ID": self.order_id,
                "Volume": self.volume,
                "Order Timestamp": str(self.timestamp),
                "Age": float(age),
            }
        else:
            return {
                "Timestamp": str(timestamp),
                "Type": order_type_str,
                "Level": level_num,
                "Price": float(price),
                "Order ID": self.order_id,
                "Volume": self.volume,
                "Order Timestamp": str(self.timestamp),
            }


class Level(Generic[Price, Volume, OrderID, Qualifiers]):
    """A price level in the limit order book.

    This class represents a single price level containing a queue of orders
    at that price. It manages order entry, cancellation, deletion, and
    execution according to price-time priority.

    Attributes:
        price: The price of this level
        queue: List of orders at this price level, ordered by time priority
    """

    def __init__(self, price: Price) -> None:
        """Initialize a price level.

        Args:
            price: The price for this level
        """
        self.price: Price = price
        self.queue: list[OrderOnBook[Volume, OrderID, Qualifiers]] = []

    def order_factory(
        self,
        order_id: OrderID,
        timestamp: Timestamp,
        volume: Volume,
        qualifs: Qualifiers | None = None,
    ) -> OrderOnBook[Volume, OrderID, Qualifiers]:
        """Create a new OrderOnBook instance.

        Factory method to create OrderOnBook objects with the specified parameters.

        Args:
            order_id: Unique identifier for the order
            timestamp: When the order was placed
            volume: Volume of the order
            qualifs: Optional qualifiers for the order

        Returns:
            OrderOnBook: A new order instance
        """
        return OrderOnBook(
            order_id=order_id, timestamp=timestamp, volume=volume, qualifs=qualifs
        )

    def print_out(self, indent: str = "", level: int = 0) -> None:
        """Print the price level information.

        Args:
            indent: Indentation string for formatting
            level: Level number for display
        """
        print(f"{indent}Price level {level}: {self.price}")
        for x in self.queue:
            x.print_out(f"{indent}  ")

    def get_orders_data(self) -> list[dict[str, Any]]:
        """Get structured data for all orders at this level.

        Returns:
            List of dictionaries containing order data
        """
        orders_data = []
        for order in self.queue:
            order_data = order.get_order_data()
            orders_data.append(order_data)
        return orders_data

    def to_records(
        self,
        order_type_str: str,
        level_num: int,
        price: Price,
        timestamp: Timestamp,
        collapse_orders: bool = False,
        show_age: bool = False,
    ) -> list[dict[str, Any]]:
        """Convert level data to structured records.

        This method provides direct access to level data without the
        overhead of CSV serialization and parsing.

        Args:
            order_type_str: Type of order (e.g., 'Ask', 'Bid')
            level_num: Price level number
            price: Price to use for the records
            timestamp: Current timestamp for the record
            collapse_orders: Whether to aggregate all orders at this level
            show_age: Whether to include age information

        Returns:
            List of dictionary records representing the level data
        """
        records = []

        if collapse_orders:
            volume = 0
            n_orders = len(self.queue)
            for order in self.queue:
                volume += order.volume

            if show_age:
                vw_age_acc = None
                age_acc = None
                for order in self.queue:
                    order_age = timestamp - order.timestamp
                    if vw_age_acc is None:
                        vw_age_acc = order_age * order.volume
                    else:
                        vw_age_acc += order_age * order.volume
                    if age_acc is None:
                        age_acc = order_age
                    else:
                        age_acc += order_age

                if vw_age_acc is not None and volume > 0:
                    vw_age = vw_age_acc / float(volume)
                else:
                    vw_age = 0.0

                if age_acc is not None and n_orders > 0:
                    age = age_acc / float(n_orders)
                else:
                    age = 0.0

                first_age = timestamp - self.queue[0].timestamp if self.queue else 0.0
                last_age = timestamp - self.queue[-1].timestamp if self.queue else 0.0

                record = {
                    "Timestamp": str(timestamp),
                    "Type": order_type_str,
                    "Level": level_num,
                    "Price": float(price),
                    "Volume": volume,
                    "N Orders": n_orders,
                    "Volume-Weighted Average Age": float(vw_age),
                    "Average Age": float(age),
                    "First Age": float(first_age),
                    "Last Age": float(last_age),
                }
            else:
                record = {
                    "Timestamp": str(timestamp),
                    "Type": order_type_str,
                    "Level": level_num,
                    "Price": float(price),
                    "Volume": volume,
                    "N Orders": n_orders,
                }
            records.append(record)
        else:
            # Individual order records
            for order in self.queue:
                order_record = order.to_record(
                    order_type_str=order_type_str,
                    level_num=level_num,
                    price=price,
                    timestamp=timestamp,
                    show_age=show_age,
                )
                records.append(order_record)

        return records

    def order_on_book(self, order_id: OrderID) -> bool:
        """Check if an order is on the book at this level.

        Args:
            order_id: The order identifier to search for

        Returns:
            bool: True if the order is found, False otherwise
        """
        for x in self.queue:
            if x.order_id == order_id:
                return True
        return False

    @property
    def volume(self) -> Volume:
        """Get the total volume at this price level.

        Returns:
            Volume: Sum of all order volumes at this level
        """
        acc: Volume | None = None
        for x in self.queue:
            if x.volume is not None:
                acc += x.volume
            else:
                acc = x.volume
        if acc is None:
            raise ValueError("No volume found")
        return acc

    def execution_price(self, volume: Volume) -> tuple[Price, Volume]:
        """Calculate the execution price for a given volume.

        Returns a tuple with the total price and the number of shares that
        can be executed, which is min(requested volume, total book volume
        at current level).

        Args:
            volume: The volume to calculate execution price for

        Returns:
            tuple[Price, Volume]: (total_price, executed_volume)
        """
        volume_acc: Volume | None = None

        for x in self.queue:
            volume_ord = x.volume
            if volume_acc is None:
                volume_acc = volume_ord
            else:
                volume_acc += volume_ord
            if volume_acc >= volume:
                volume_acc = volume
                break

        return (self.price * volume_acc, volume_acc)

    def find_order_on_book(self, order_id: OrderID) -> int:
        """Find the position of an order in the queue.

        Args:
            order_id: The order identifier to search for

        Returns:
            int: Index of the order in the queue, or -1 if not found
        """
        for x in range(len(self.queue)):
            if self.queue[x].order_id == order_id:
                return x
        return -1

    def cancel_quote(
        self, order_id: OrderID, volume: Volume, i: int | None = None
    ) -> None:
        """Cancel a portion of an order.

        Cancels the specified volume from an order. If the order volume
        becomes zero, the order is removed from the queue.

        Args:
            order_id: The order identifier to cancel
            volume: The volume to cancel
            i: Optional index of the order in the queue

        Raises:
            Exception: If the order is not found at this level
            VolumeInconsistencyException: If cancel volume exceeds order volume
        """
        # Find the quote, and delete it (make sure volumes match)
        if i is None:
            i = self.find_order_on_book(order_id)
            if i == -1:
                raise OrderNotFoundError(f"Order ID {order_id} not on level")
        # Check for consistency in volume
        if self.queue[i].volume < volume:
            book_vol = self.queue[i].volume
            del self.queue[i]
            raise VolumeInconsistencyException(
                "Level:cancel_quote",
                f"Cancel volume ({volume}) larger than book volume ({book_vol}) for order ID {order_id}",
                order_id,
            )
        # Delete order
        elif self.queue[i].volume == volume:
            del self.queue[i]
        else:
            self.queue[i].volume -= volume

    def delete_quote(self, order_id: OrderID, i: int | None = None) -> bool:
        """Delete an entire order from the queue.

        Args:
            order_id: The order identifier to delete
            i: Optional index of the order in the queue

        Returns:
            bool: True on successful deletion

        Raises:
            Exception: If the order is not found at this level
        """
        if i is None:
            i = self.find_order_on_book(order_id)
            if i == -1:
                raise OrderNotFoundError(f"Order ID {order_id} not on level")

        # Delete order
        del self.queue[i]
        return True

    def enter_quote(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        qualifs: Qualifiers | None = None,
    ) -> None:
        """Enter a new quote at the back of the queue.

        Adds a new order to the end of the queue (time priority).

        Args:
            timestamp: When the order was placed
            volume: Volume of the order
            order_id: Unique identifier for the order
            qualifs: Optional qualifiers for the order
        """
        self.queue.append(self.order_factory(order_id, timestamp, volume, qualifs))

    def enter_quote_out_of_order(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        qualifs: Qualifiers | None = None,
    ) -> None:
        """Enter a quote in the queue according to timestamp priority.

        Inserts the order at the correct position based on timestamp,
        maintaining time priority order.

        Args:
            timestamp: When the order was placed
            volume: Volume of the order
            order_id: Unique identifier for the order
            qualifs: Optional qualifiers for the order
        """
        i = 0
        for x in self.queue:
            if x.timestamp < timestamp:
                i = i + 1
            else:
                continue

        self.queue.insert(i, self.order_factory(order_id, timestamp, volume, qualifs))

    def enter_quote_at_position(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        position: int,
        check_position: bool,
        qualifs: Qualifiers | None = None,
    ) -> None:
        """Enter a quote at a specific position in the queue.

        Inserts the order at the specified position, optionally checking
        if the position is consistent with timestamp priority.

        Args:
            timestamp: When the order was placed
            volume: Volume of the order
            order_id: Unique identifier for the order
            position: Position in the queue (1-based)
            check_position: Whether to verify position consistency
            qualifs: Optional qualifiers for the order

        Raises:
            ExecutionPriorityException: If position check fails
        """
        raise_error = False
        i = 0
        if check_position:
            for x in self.queue:
                if x.timestamp <= timestamp:
                    i = i + 1
                else:
                    continue
            if i != (position - 1):
                raise_error = True

        self.queue.insert(
            position - 1, self.order_factory(order_id, timestamp, volume, qualifs)
        )

        if raise_error:
            raise ExecutionPriorityException(
                "Level:enter_quote_at_position",
                f"Order ID {order_id} should be at position {i}, not {position - 1}.",
                timestamp,
                order_id,
                None,
            )

    def execute_trade(
        self, order_id: OrderID, volume: Volume, timestamp: Timestamp | None = None
    ) -> None:
        """
        Execute the trade with priority.

        :param order_id:
        :param volume:
        :param timestamp:
        :return:
        """
        if self.queue[0].order_id != order_id:
            raise ExecutionPriorityException(
                "Level:execute_trade",
                f"Order ID {order_id} not first in line, {self.queue[0].order_id} is.",
                timestamp,
                order_id,
                self.queue[0].order_id,
            )
        if self.queue[0].volume > volume:
            self.queue[0].volume -= volume
        elif self.queue[0].volume == volume:
            del self.queue[0]
        else:
            book_vol = str(self.queue[0].volume)
            del self.queue[0]
            raise VolumeInconsistencyException(
                "Level:execute_trade",
                f"Volume ({volume}) larger than book volume ({book_vol}) for order {order_id}",
                order_id,
            )

    def execute_trade_price(
        self, order_id: OrderID, volume: Volume, timestamp: Timestamp | None = None
    ) -> None:
        """
        Execute the trade, bypass priority priority.


        :param order_id:
        :param volume:
        :param timestamp:
        :return:
        """
        # Find the order
        order = None
        for x in range(len(self.queue)):
            if self.queue[x].order_id == order_id:
                order = x
                break

        if order is None:
            raise OrderNotFoundError(f"Order ID {order_id} not in queue")
        if self.queue[order].volume > volume:
            self.queue[order].volume -= volume
        elif self.queue[order].volume == volume:
            del self.queue[order]
        else:
            book_vol = str(self.queue[order].volume)
            del self.queue[order]
            raise VolumeInconsistencyException(
                "Level:execute_trade_price",
                f"Volume ({volume}) larger than book volume ({book_vol})",
                order_id,
            )
