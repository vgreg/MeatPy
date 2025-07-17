from copy import deepcopy
from decimal import Decimal
from enum import Enum
from math import log
from typing import Any, Generic

from .level import ExecutionPriorityException, Level
from .timestamp import Timestamp
from .types import OrderID, Price, Qualifiers, TradeRef, Volume


class InexistantValueException(Exception):
    """Exception raised when a value does not exist in the limit order book.

    This exception is raised when attempting to access values that are not
    available in the current state of the limit order book.
    """

    pass


class ExecutionPriorityExceptionList(Exception):
    """Exception raised when multiple execution priority errors occur.

    This exception is raised when there are multiple execution priority
    violations that need to be handled together.
    """

    pass


class InvalidPriceTypeError(Exception):
    """Exception raised when an invalid price type is encountered.

    This exception is raised when the price type is not supported
    by the limit order book operations.
    """

    pass


class OrderNotFoundError(Exception):
    """Exception raised when an order is not found in the limit order book.

    This exception is raised when attempting to perform operations on an order
    that does not exist in the specified price level or queue.
    """

    pass


class InvalidOrderTypeError(Exception):
    """Exception raised when an invalid order type is encountered.

    This exception is raised when the order type is not supported
    by the limit order book operations.
    """

    pass


class InvalidPositionError(Exception):
    """Exception raised when an invalid position is specified.

    This exception is raised when the position specified for order
    placement is not valid or possible.
    """

    pass


class OrderType(Enum):
    """Enumeration for order types in the limit order book.

    Attributes:
        ASK: Sell order type (value: 0)
        BID: Buy order type (value: 1)
    """

    ASK = 0
    BID = 1


class LimitOrderBook(Generic[Price, Volume, OrderID, TradeRef, Qualifiers]):
    """A snapshot of a limit order book.

    The handling of orders (enter, execute, revise) is standard
    and should apply to any exchange that applies price and
    time preference for execution of orders on the book.
    """

    def __init__(self, timestamp: Timestamp, timestamp_inc: int = 0) -> None:
        """Initialize the limit order book with a timestamp and empty order queues.

        If there are more than one LimitOrderBook at the same timestamp,
        timestamp_inc is used to rank them in chronological order (first event
        is 0, second is 1, etc.)

        Args:
            timestamp: Timestamp of the limit order book.
            timestamp_inc: Rank of event at timestamp, defaults to 0.
        """
        self.timestamp: Timestamp = timestamp
        self.timestamp_inc: int = timestamp_inc
        self.bid_levels: list[Level] = []
        self.ask_levels: list[Level] = []

        self.decimals_adj: int | Decimal | None = (
            None  # Price are divided by this number
        )

        self.execution_errors_buffer: list[
            ExecutionPriorityException
        ] = []  # Buffer for executions out of order

    def print_out(self, indent: str = "") -> None:
        """Print the content of the limit order book.

        Args:
            indent: String to prepend to each line for indentation, defaults to "".
        """
        print(
            f"{indent}LOB Snapshot: {self.timestamp},{self.timestamp_inc} -------------"
        )
        print(f"{indent} Bid:")
        i = 0
        for x in self.bid_levels:
            i += 1
            x.print_out(f"{indent}  ", i)
        print(f"{indent} Ask:")
        i = 0
        for x in self.ask_levels:
            i += 1
            x.print_out(f"{indent}  ", i)

    def create_level_from_price(self, price: Price) -> Level:
        """Create a new Level instance with the given price.

        Args:
            price: The price for the new level.

        Returns:
            A new Level instance.
        """
        return Level(price=price)

    def copy(self, max_level: int | None = None) -> "LimitOrderBook":
        """Create a deep copy of the limit order book.

        Args:
            max_level: Maximum number of levels to copy, defaults to None (copy all).

        Returns:
            A deep copy of the limit order book.
        """
        new_lob = LimitOrderBook(deepcopy(self.timestamp), self.timestamp_inc)
        new_lob.timestamp_inc = self.timestamp_inc
        new_lob.decimals_adj = self.decimals_adj
        if max_level is None:
            new_lob.ask_levels = deepcopy(self.ask_levels)
            new_lob.bid_levels = deepcopy(self.bid_levels)
        else:
            i = 0
            while i < max_level:
                if i < len(self.ask_levels):
                    new_lob.ask_levels.append(deepcopy(self.ask_levels[i]))
                if i < len(self.bid_levels):
                    new_lob.bid_levels.append(deepcopy(self.bid_levels[i]))
                i += 1
        return new_lob

    def get_bid_levels(self, max_depth: int | None = None) -> list[Level]:
        """Get bid levels up to specified depth.

        Args:
            max_depth: Maximum number of levels to return (None for all)

        Returns:
            List of bid levels
        """
        if max_depth is None:
            return self.bid_levels[:]
        return self.bid_levels[:max_depth]

    def get_ask_levels(self, max_depth: int | None = None) -> list[Level]:
        """Get ask levels up to specified depth.

        Args:
            max_depth: Maximum number of levels to return (None for all)

        Returns:
            List of ask levels
        """
        if max_depth is None:
            return self.ask_levels[:]
        return self.ask_levels[:max_depth]

    def to_records(
        self,
        collapse_orders: bool = False,
        show_age: bool = False,
        max_depth: int | None = None,
    ) -> list[dict[str, Any]]:
        """Convert limit order book to structured records.

        This method provides direct access to the limit order book data
        without the overhead of CSV serialization and parsing.

        Args:
            collapse_orders: Whether to aggregate orders by level
            show_age: Whether to include order age information
            max_depth: Maximum depth of levels to include (None for all)

        Returns:
            List of dictionary records representing the book state
        """
        records = []

        # Process ask levels
        ask_levels = self.get_ask_levels(max_depth)
        for level_num, level in enumerate(ask_levels, 1):
            level_records = level.to_records(
                order_type_str="Ask",
                level_num=level_num,
                price=self.adjust_price(level.price),
                timestamp=self.timestamp,
                collapse_orders=collapse_orders,
                show_age=show_age,
            )
            records.extend(level_records)

        # Process bid levels
        bid_levels = self.get_bid_levels(max_depth)
        for level_num, level in enumerate(bid_levels, 1):
            level_records = level.to_records(
                order_type_str="Bid",
                level_num=level_num,
                price=self.adjust_price(level.price),
                timestamp=self.timestamp,
                collapse_orders=collapse_orders,
                show_age=show_age,
            )
            records.extend(level_records)

        return records

    #### Built-in measures #######

    def adjust_price(self, price: Price) -> Decimal:
        """Adjust the price according to the decimals_adj setting.

        Args:
            price: The price to adjust.

        Returns:
            The adjusted price as a Decimal.
        """
        return (
            Decimal(price) / self.decimals_adj
            if self.decimals_adj is not None
            else Decimal(price)
        )

    @property
    def bid_ask_spread(self) -> Decimal:
        """Return the bid-ask spread.

        Returns:
            The bid-ask spread as a Decimal.

        Raises:
            InexistantValueException: If there is no bid-ask spread available.
        """
        try:
            return self.adjust_price(
                self.ask_levels[0].price - self.bid_levels[0].price
            )
        except IndexError:
            raise InexistantValueException(
                "LimitOrderBook:bid_ask_spread", "There is no bid-ask spread"
            )

    @property
    def mid_quote(self) -> Decimal:
        """Return the mid quote.

        Returns:
            The mid quote as a Decimal.

        Raises:
            InexistantValueException: If there is no bid-ask spread available.
        """
        try:
            return Decimal(
                self.adjust_price(self.ask_levels[0].price + self.bid_levels[0].price)
                / 2
            )
        except IndexError:
            raise InexistantValueException(
                "LimitOrderBook:mid quote", "There is no bid-ask spread"
            )

    @property
    def quote_slope(self) -> float:
        """Return the slope between the two levels of depth between the ask and the bid.

        Flatter the slope is, the more liquid is the market.

        Returns:
            The quote slope as a float.

        Raises:
            InexistantValueException: If there is missing bid or ask price or volume.
        """
        try:
            return float(self.bid_ask_spread) / (
                log(self.ask_levels[0].volume) + log(self.bid_levels[0].volume)
            )
        except IndexError:
            raise InexistantValueException(
                "LimitOrderBook:quote_slope", "There missing bid or ask price or volume"
            )

    @property
    def log_quote_slope(self) -> float:
        """Return the log of the slope between the two levels of depth between the ask and the bid.

        Flatter the slope is, the more liquid is the market.

        Returns:
            The effective spread in percent as a float.

        Raises:
            InexistantValueException: If there is no bid-ask spread available.
        """
        try:
            return float(
                (log(float(self.ask_levels[0].price / self.bid_levels[0].price)))
                / (log(self.ask_levels[0].volume) + log(self.bid_levels[0].volume))
            )
        except IndexError:
            raise InexistantValueException(
                "LimitOrderBook:log_quote_slope", "There is no bid-ask spread"
            )

    @property
    def best_bid(self) -> Decimal:
        """Return the best bid.

        Returns:
            The best bid as a Decimal.

        Raises:
            InexistantValueException: If there is no best bid available.
        """
        try:
            return self.adjust_price(self.bid_levels[0].price)
        except IndexError:
            raise InexistantValueException(
                "LimitOrderBook:best_bid", "There is no best bid"
            )

    @property
    def best_ask(self) -> Decimal:
        """Return the best ask.

        Returns:
            The best ask as a Decimal.

        Raises:
            InexistantValueException: If there is no best ask available.
        """
        try:
            return self.adjust_price(self.ask_levels[0].price)
        except IndexError:
            raise InexistantValueException(
                "LimitOrderBook:best_ask", "There is no best ask"
            )

    def buy_execution_price(self, volume: Volume) -> tuple[Decimal, int]:
        """Compute the execution price for a buy order of a certain volume.

        Returns a tuple, with the first element being the total price and
        the second element the number of shares, which is
        min(requested volume, total book volume).

        Args:
            volume: The volume to execute.

        Returns:
            A tuple containing (total_price, executed_volume).
        """
        volume_acc = 0
        price_acc = 0

        for x in self.ask_levels:
            (price_lvl, volume_lvl) = x.execution_price(volume - volume_acc)
            price_acc += price_lvl
            volume_acc += volume_lvl
            if volume_acc == volume:
                break

        return (self.adjust_price(price_acc), volume_acc)

    def sell_execution_price(self, volume: Volume) -> tuple[Decimal, int]:
        """Compute the execution price for a sell order of a certain volume.

        Returns a tuple, with the first element being the total price and
        the second element the number of shares, which is
        min(requested volume, total book volume).

        Args:
            volume: The volume to execute.

        Returns:
            A tuple containing (total_price, executed_volume).
        """
        volume_acc = 0
        price_acc = 0

        for x in self.bid_levels:
            (price_lvl, volume_lvl) = x.execution_price(volume - volume_acc)
            price_acc += price_lvl
            volume_acc += volume_lvl
            if volume_acc == volume:
                break

        return (self.adjust_price(price_acc), volume_acc)

    #### Companion methods

    def order_on_book(
        self, order_id: OrderID, order_type: OrderType | None = None
    ) -> bool:
        """Indicate if the order_id is on the book.

        Args:
            order_id: Order ID (exchange-specific).
            order_type: Specific order type to check, defaults to None (check both).

        Returns:
            True if the order is on the book, False otherwise.
        """
        if order_type is None:
            if self.ask_order_on_book(order_id):
                return True
            elif self.bid_order_on_book(order_id):
                return True
            else:
                return False
        elif order_type == OrderType.ASK:
            if self.ask_order_on_book(order_id):
                return True
            else:
                return False
        elif order_type == OrderType.BID:
            if self.bid_order_on_book(order_id):
                return True
            else:
                return False

    def ask_order_on_book(self, order_id: OrderID) -> bool:
        """Indicate if the order_id is on the ask book.

        Args:
            order_id: Order ID (exchange-specific).

        Returns:
            True if the order is on the ask book, False otherwise.
        """
        for x in self.ask_levels:
            if x.order_on_book(order_id):
                return True
        return False

    def bid_order_on_book(self, order_id: OrderID) -> bool:
        """Indicate if the order_id is on the bid book.

        Args:
            order_id: Order ID (exchange-specific).

        Returns:
            True if the order is on the bid book, False otherwise.
        """
        for x in self.bid_levels:
            if x.order_on_book(order_id):
                return True
        return False

    def find_order_type(self, order_id: OrderID) -> OrderType:
        """Find the type for an order on the book.

        Args:
            order_id: Order ID to find the type for.

        Returns:
            The OrderType (ASK or BID) of the order.

        Raises:
            OrderNotFoundError: If the order is not found on the book.
        """
        if self.bid_order_on_book(order_id):
            return OrderType.BID
        elif self.ask_order_on_book(order_id):
            return OrderType.ASK
        else:
            raise OrderNotFoundError(f"Order not found: {order_id!r}")

    def find_order(
        self, order_id: OrderID, order_type: OrderType | None = None
    ) -> tuple[list[Level], int, int]:
        """Find the order for an order on the book with possibly known type.

        Returns a tuple with queue as the first element, level as second,
        rank on level as third.

        Args:
            order_id: Order ID to find.
            order_type: Specific order type to search, defaults to None (search both).

        Returns:
            A tuple containing (queue, level_index, rank_on_level).

        Raises:
            OrderNotFoundError: If the order is not found on the book.
            InvalidOrderTypeError: If an unknown order type is specified.
        """
        # By default, look at order starting from top of book.
        if order_type is None:
            i = 0
            while i < max(len(self.ask_levels), len(self.bid_levels)):
                if i < len(self.ask_levels):
                    j = self.ask_levels[i].find_order_on_book(order_id)
                    if j != -1:
                        return (self.ask_levels, i, j)
                if i < len(self.bid_levels):
                    j = self.bid_levels[i].find_order_on_book(order_id)
                    if j != -1:
                        return (self.bid_levels, i, j)
                i += 1
        else:
            if order_type == OrderType.ASK:
                queue = self.ask_levels
            elif order_type == OrderType.BID:
                queue = self.bid_levels
            else:
                raise InvalidOrderTypeError(f"Unknown order type: {order_type}")
            i = 0
            while i < len(queue):
                j = queue[i].find_order_on_book(order_id)
                if j != -1:
                    return (queue, i, j)
                i += 1

        raise OrderNotFoundError(f"Quote ID ({order_id!r}) missing from queue")

    #### Order and trade processing

    def enter_quote(
        self,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType,
        qualifs: Qualifiers | None = None,
    ) -> None:
        """Enter the quote in the appropriate queue in the right order.

        Implement price and time priority.
        Assumes the current list is ordered (0=highest priority).

        Args:
            timestamp: Timestamp of the quote entry.
            price: Price of the quote.
            volume: Volume of the quote.
            order_id: Order ID for the quote.
            order_type: Type of the order (ASK or BID).
            qualifs: Additional qualifications for the quote, defaults to None.
        """
        if order_type == OrderType.ASK:
            queue = self.ask_levels
            ask = True
        else:
            queue = self.bid_levels
            ask = False

        i = 0
        if ask:
            while i < len(queue) and price > queue[i].price:
                i += 1
        else:
            while i < len(queue) and price < queue[i].price:
                i += 1

        # If the price level does not exist, create it!
        if i == len(queue) or queue[i].price != price:
            queue.insert(i, self.create_level_from_price(price))
        # Enter the quote on the level
        queue[i].enter_quote(timestamp, volume, order_id, qualifs)

    def enter_quote_out_of_order(
        self, timestamp, price, volume, order_id, order_type, qualifs=None
    ) -> None:
        """Enter the quote in the appropriate queue in the right order.

        Implement price and time priority.
        Assumes the current list is ordered (0=highest priority).
        Does not assume the input timestamp is the most recent.

        Args:
            timestamp: Timestamp of the quote entry.
            price: Price of the quote.
            volume: Volume of the quote.
            order_id: Order ID for the quote.
            order_type: Type of the order (ASK or BID).
            qualifs: Additional qualifications for the quote, defaults to None.
        """
        if order_type == OrderType.ASK:
            queue = self.ask_levels
            ask = True
        else:
            queue = self.bid_levels
            ask = False

        i = 0
        if ask:
            while i < len(queue) and price > queue[i].price:
                i += 1
        else:
            while i < len(queue) and price < queue[i].price:
                i += 1

        # If the price level does not exist, create it!
        if i == len(queue) or queue[i].price != price:
            queue.insert(i, self.create_level_from_price(price))
        # Enter the quote on the level
        queue[i].enter_quote_out_of_order(timestamp, volume, order_id, qualifs)

    def enter_quote_at_position(
        self,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType,
        position: int,
        check_priority: bool,
        qualifs=None,
    ) -> None:
        """Enter the quote in the appropriate queue at a specific position.

        Enter the quote in the appropriate queue in the right order (global
        order on the book, not only on level).
        Check for price and time priority if required.
        Assumes the current list is ordered (0=highest priority).

        Args:
            timestamp: Timestamp of the quote entry.
            price: Price of the quote.
            volume: Volume of the quote.
            order_id: Order ID for the quote.
            order_type: Type of the order (ASK or BID).
            position: Global position on the book.
            check_priority: Whether to check priority constraints.
            qualifs: Additional qualifications for the quote, defaults to None.

        Raises:
            InvalidPositionError: If the specified position is not possible.
        """
        if order_type == OrderType.ASK:
            queue = self.ask_levels
            ask = True
        else:
            queue = self.bid_levels
            ask = False

        i = 0
        if ask:
            while i < len(queue) and price > queue[i].price:
                i += 1
        else:
            while i < len(queue) and price < queue[i].price:
                i += 1

        # If the price level does not exist, create it!
        if i == len(queue) or queue[i].price != price:
            queue.insert(i, self.create_level_from_price(price))

        # Compute the number of positions in front
        pre_positions = 0
        for j in range(i):
            pre_positions += len(queue[j].queue)

        level_position = position - pre_positions
        if level_position < 1:
            raise InvalidPositionError(f"Level position not possible: {level_position}")

        # Enter the quote on the level
        queue[i].enter_quote_at_position(
            timestamp, volume, order_id, level_position, check_priority, qualifs
        )

    def cancel_quote(
        self, volume: Volume, order_id: OrderID, order_type: OrderType | None = None
    ) -> None:
        """Delete the quote from the appropriate queue.

        Find the quote, and delete it (make sure volumes match).

        Args:
            volume: Volume to cancel.
            order_id: Order ID to cancel.
            order_type: Specific order type to search, defaults to None.

        Raises:
            OrderNotFoundError: If the order is not found.
        """
        (queue, i, j) = self.find_order(order_id, order_type)

        try:
            queue[i].cancel_quote(order_id, volume, j)
        finally:
            # Delete empty levels
            if len(queue[i].queue) == 0:
                del queue[i]

    def delete_quote(
        self, order_id: OrderID, order_type: OrderType | None = None
    ) -> None:
        """Delete the quote from the appropriate queue.

        Find the quote, and delete it.

        Args:
            order_id: Order ID to delete.
            order_type: Specific order type to search, defaults to None.

        Raises:
            OrderNotFoundError: If the order is not found.
        """
        (queue, i, j) = self.find_order(order_id, order_type)

        try:
            queue[i].delete_quote(order_id, j)
        finally:
            # Delete empty levels
            if len(queue[i].queue) == 0:
                del queue[i]

    def execute_trade(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Apply the effect of the execution on the book.

        Make sure volume and ID are consistent with current order of book.
        Order should be next in line on book, unless a price is specified.

        Args:
            timestamp: Timestamp of the trade execution.
            volume: Volume to execute.
            order_id: Order ID to execute.
            order_type: Specific order type to search, defaults to None.

        Raises:
            OrderNotFoundError: If the order is not found.
            ExecutionPriorityExceptionList: If there are execution priority violations.
        """
        (queue, i, j) = self.find_order(order_id, order_type)
        # Should execute at the "best price"
        try:
            queue[0].execute_trade(order_id, volume, timestamp)
            if len(self.execution_errors_buffer) > 0:
                # If we reach here, execution was successful, so we remove
                # the false positives and print out the remaining errors.
                errors_to_raise = []
                new_errors = []
                for e in self.execution_errors_buffer:
                    if e.args[2] == timestamp:
                        if e.args[4] != order_id:
                            new_errors.append(e)
                    else:
                        errors_to_raise.append(e)
                self.execution_errors_buffer = new_errors
                if len(errors_to_raise) > 0:
                    self.execution_errors_buffer = []
                    # Delete empty levels
                    if len(queue[0].queue) == 0:
                        del queue[0]
                    raise ExecutionPriorityExceptionList(
                        "LimitOrderBook:execute_trade", errors_to_raise
                    )
        except ExecutionPriorityException as e:
            if not self.skip_exception(e):
                self.execution_errors_buffer.append(e)
            self.execute_trade_price(
                timestamp=timestamp, volume=volume, order_id=order_id
            )
        finally:
            # Delete empty levels
            if len(queue[0].queue) == 0:
                del queue[0]

    def skip_exception(self, e: Exception) -> bool:
        """Indicate if the exception should be skipped.

        Args:
            e: The exception to check.

        Returns:
            True if the exception should be skipped, False otherwise.
        """
        return False

    def find_liquidity_maker(self, ask_id: OrderID, bid_id: OrderID) -> OrderID:
        """Find which of the two orders is already on the book.

        Args:
            ask_id: The ask order ID.
            bid_id: The bid order ID.

        Returns:
            The OrderID of the order that is already on the book (the maker).

        Raises:
            ValueError: If it cannot be determined which order is the maker.
        """
        if not self.ask_order_on_book(ask_id):  # Sell order
            return bid_id
        elif not self.bid_order_on_book(bid_id):  # Buy order
            return ask_id
        else:
            raise ValueError("Could not determine maker/taker")

    def execute_trade_price(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Apply the effect of the execution on the book at a specific price.

        Make sure volume and ID are consistent with current order of book.
        Order should be next in line on book, unless a price is specified.

        Args:
            timestamp: Timestamp of the trade execution.
            volume: Volume to execute.
            order_id: Order ID to execute.
            order_type: Specific order type to search, defaults to None.

        Raises:
            OrderNotFoundError: If the order is not found.
        """
        (queue, i, j) = self.find_order(order_id, order_type)

        queue[i].execute_trade_price(order_id, volume, timestamp)
        # Delete empty levels
        if len(queue[i].queue) == 0:
            del queue[i]

    def end_of_day(self) -> None:
        """Identify issues if this is the end of trading day.

        Raises:
            ExecutionPriorityExceptionList: If there are remaining execution errors.
        """
        # 1) Raise remaining exceptions.
        if len(self.execution_errors_buffer) > 0:
            raise ExecutionPriorityExceptionList(
                "LimitOrderBook:execute_trade", self.execution_errors_buffer
            )
