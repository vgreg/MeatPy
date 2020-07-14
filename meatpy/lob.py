"""lob.py: A snapshot of the limit order book."""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

from math import log
from meatpy.level import Level, ExecutionPriorityException
from copy import deepcopy


class InexistantValueException(Exception):
    pass

class ExecutionPriorityExceptionList(Exception):
    pass


class LimitOrderBook:
    """A snapshot a a limit order book

    The handling of orders (enter, execute, revise) is standard
    and should apply to any exchange that applies price and
    time preference for execution of orders on the book.
    """
    def __init__(self, timestamp, timestamp_inc=0):
        """Initialize the object with a timestamp and event_type and empty
        order queues.

        If there are more than one LimitOrderBook at the same timestamp,
        timestamp_inc is used to rank them in chronological order (first event
        is 0, second is 1, etc.)

        :param timestamp: timestamp of the limit order book
        :type timestamp: datetime
        :param timestamp_inc: rank of event at timestamp
        :type timestamp_inc: int
        """
        self.timestamp = timestamp
        self.timestamp_inc = timestamp_inc
        self.bid_levels = []
        self.ask_levels = []

        self.decimals_adj = None  # Price are divided by this number

        self.execution_errors_buffer = []  # Buffer for executions out of order

    def print_out(self, indent=''):
        """Print the content of the limit order book."""
        print( indent + 'LOB Snapshot: ' + 
            str(self.timestamp) + ',' + 
            str(self.timestamp_inc) + ' -------------')
        print( indent + ' Bid:')
        i = 0
        for x in self.bid_levels:
            i += 1
            x.print_out(indent + '  ', i)
        print( indent + ' Ask:')
        i = 0
        for x in self.ask_levels:
            i += 1
            x.print_out(indent + '  ', i)

    # Common type definitions. Note: Also redefined in MarketProcessor.
    ask_type = 0
    bid_type = 1

    def level_factory(self, price):
        return Level(price=price)

    def copy(self, max_level=None):
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

    def write_csv(self, file, collapse_orders=False, show_age=False):
        """Write rows for the content of the LOB"""
        i = 1
        for x in self.ask_levels:
            x.write_csv(file, self.timestamp, "Ask", i, collapse_orders,
                        self.adjust_price(x.price), show_age)
            i += 1
        i = 1
        for x in self.bid_levels:
            x.write_csv(file, self.timestamp, "Bid", i, collapse_orders,
                        self.adjust_price(x.price), show_age)
            i += 1

#### Built-in measures #######

    def adjust_price(self, price):
        if self.decimals_adj is None:
            return price
        return price / self.decimals_adj

    def bid_ask_spread(self):
        """Return the bid-ask spread

        :returns: bid ask spread
        :rtype: same as price format
        """
        try:
            return self.adjust_price(self.ask_levels[0].price -
                                     self.bid_levels[0].price)
        except IndexError:
            raise InexistantValueException('LimitOrderBook:bid_ask_spread',
                                           'There is no bid-ask spread')

    def mid_quote(self):
        """Return the mid quote

        :returns: mid quote
        :rtype: same as price format
        """
        try:
            return self.adjust_price(float(self.ask_levels[0].price +
                                           self.bid_levels[0].price))/2.0
        except IndexError:
            raise InexistantValueException('LimitOrderBook:mid quote',
                                           'There is no bid-ask spread')

    def quote_slope(self):
        """Return the slope between the two levels of depth between the ask and
        the bid. Flatter the slope is, the more liquid is the market.

        :returns: quote slope
        """
        try:
            return (float(self.bid_ask_spread()) /
                    (log(self.ask_levels[0].volume()) +
                     log(self.bid_levels[0].volume())))
        except IndexError:
            raise InexistantValueException('LimitOrderBook:quote_slope',
                                           'There missing bid or ask price or volume')

    def log_quote_slope(self):
        """Return the log of the slope between the two levels of depth between
        the ask and the bid. Flatter the slope is, the more liquid is the
        market.

        :returns: effective spread in percent
        """
        try:
            return float((log(float(self.ask_levels[0].price /
                         self.bid_levels[0].price))) /
                         (log(self.ask_levels[0].volume()) +
                          log(self.bid_levels[0].volume())))
        except IndexError:
            raise InexistantValueException('LimitOrderBook:log_quote_slope',
                                           'There is no bid-ask spread')

    def best_bid(self):
        """Return the best bid

        :returns: best bid
        :rtype: same as price format
        """
        try:
            return self.adjust_price(self.bid_levels[0].price)
        except IndexError:
            raise InexistantValueException('LimitOrderBook:best_bid',
                                           'There is no best bid')

    def best_ask(self):
        """Return the best ask

        :returns: best ask
        :rtype: same as price format
        """
        try:
            return self.adjust_price(self.ask_levels[0].price)
        except IndexError:
            raise InexistantValueException('LimitOrderBook:best_ask',
                                           'There is no best ask')

    def buy_execution_price(self, volume):
        """Compute the execution price for a buy order of a certain volume.

        Returns a tuple, with the first element being the total price and
        the second element the number of shares, which is
        min(requested volume, total book volume)"""
        volume_acc = 0
        price_acc = 0

        for x in self.ask_levels:
            (price_lvl, volume_lvl) = x.execution_price(volume-volume_acc)
            price_acc += price_lvl
            volume_acc += volume_lvl
            if volume_acc == volume:
                break

        return (self.adjust_price(price_acc), volume_acc)

    def sell_execution_price(self, volume):
        """Compute the execution price for a sell order of a certain volume.

        Returns a tuple, with the first element being the total price and
        the second element the number of shares, which is
        min(requested volume, total book volume)"""
        volume_acc = 0
        price_acc = 0

        for x in self.bid_levels:
            (price_lvl, volume_lvl) = x.execution_price(volume-volume_acc)
            price_acc += price_lvl
            volume_acc += volume_lvl
            if volume_acc == volume:
                break

        return (self.adjust_price(price_acc), volume_acc)

#### Companion methods

    def order_on_book(self, order_id, order_type=None):
        """Indicate if the order_id is on the book.

        :param order_id: Order ID (exchange-specific)
        :type order_id: int or str
        :returns: whether the order is on the book
        :rtype: bool
        """
        if order_type is None:
            if self.ask_order_on_book(order_id):
                return True
            elif self.bid_order_on_book(order_id):
                return True
            else:
                return False
        elif order_type == self.ask_type:
            if self.ask_order_on_book(order_id):
                return True
            else:
                return False
        elif order_type == self.bid_type:
            if self.bid_order_on_book(order_id):
                return True
            else:
                return False
        else:
            raise Exception('LimitOrderBook:order_on_book',
                            'Unknown order type: ' + order_type)

    def ask_order_on_book(self, order_id):
        """Indicate if the order_id is on the ask book.

        :param order_id: Order ID (exchange-specific)
        :type order_id: int or str
        :returns: whether the order is on the book
        :rtype: bool
        """
        for x in self.ask_levels:
            if x.order_on_book(order_id):
                return True
        return False

    def bid_order_on_book(self, order_id):
        """Indicate if the order_id is on the bid book.

        :param order_id: Order ID (exchange-specific)
        :type order_id: int or str
        :returns: whether the order is on the book
        :rtype: bool
        """
        for x in self.bid_levels:
            if x.order_on_book(order_id):
                return True
        return False

    def find_order_type(self, order_id):
        """Find the type for an order on the book.

        Returns either 0 or 1."""
        if self.bid_order_on_book(order_id):
            return self.bid_type
        elif self.ask_order_on_book(order_id):
            return self.ask_type
        else:
            raise Exception('LimitOrderBook:find_order_type',
                            'Order not found: ' + str(order_id))

    def find_order(self, order_id, order_type=None):
        """Find the order for an order on the book with possibly known type.

        Returns a tuple with queue as the first element, level as second,
        rank on level as third."""
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
            if order_type == self.ask_type:
                queue = self.ask_levels
            elif order_type == self.bid_type:
                queue = self.bid_levels
            else:
                raise Exception('LimitOrderBook:find_order',
                                'Unknown order type: '+str(order_type))
            i = 0
            while i < len(queue):
                j = queue[i].find_order_on_book(order_id)
                if j != -1:
                        return (queue, i, j)
                i += 1

        raise Exception('LimitOrderBook:find_order_with_type',
                        'Quote ID (' + str(order_id) + ') missing from queue')

#### Order and trade processing

    def enter_quote(self, timestamp, price, volume, order_id, order_type,
                    qualifs=None):
        """Enter the quote in the appropriate queue in the right order

        Implement price and time priority
        Assumes the current list is ordered (0=highest priority)
        """
        if order_type == self.ask_type:
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
        if (i == len(queue) or
                queue[i].price != price):
            queue.insert(i, self.level_factory(price))
        # Enter the quote on the level
        queue[i].enter_quote(timestamp, volume, order_id, qualifs)

    def enter_quote_out_of_order(self, timestamp, price, volume, order_id,
                                 order_type, qualifs=None):
        """Enter the quote in the appropriate queue in the right order

        Implement price and time priority
        Assumes the current list is ordered (0=highest priority)
        Does not assume the input timestamp is the most recent.
        """
        if order_type == self.ask_type:
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
        if (i == len(queue) or
                queue[i].price != price):
            queue.insert(i, self.level_factory(price))
        # Enter the quote on the level
        queue[i].enter_quote_out_of_order(timestamp, volume, order_id,
                                          qualifs)

    def enter_quote_at_position(self, timestamp, price, volume, order_id,
                                order_type, position, check_priority,
                                qualifs=None):
        """Enter the quote in the appropriate queue in the right order (global
        order on the book, no only on level)

        Check for price and time priority if required
        Assumes the current list is ordered (0=highest priority)
        """
        if order_type == self.ask_type:
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
        if (i == len(queue) or
                queue[i].price != price):
            queue.insert(i, self.level_factory(price))

        # Compute the number of positions in front
        pre_positions = 0
        for j in range(i):
            pre_positions += len(queue[j].queue)

        level_position = position - pre_positions
        if level_position < 1:
            raise Exception('LimitOrderBook:enter_quote_at_position',
                            'Level position not possible: ' + str(level_position))

        # Enter the quote on the level
        queue[i].enter_quote_at_position(timestamp, volume, order_id,
                                         level_position, check_priority,
                                         qualifs)

    def cancel_quote(self, volume, order_id, order_type=None):
        """Delete the quote from the appropriate queue

        Find the quote, and delete it (make sure volumes match)
        """
        (queue, i, j) = self.find_order(order_id, order_type)

        try:
            queue[i].cancel_quote(order_id, volume, j)
        finally:
            # Delete empty levels
            if len(queue[i].queue) == 0:
                del queue[i]

    def delete_quote(self, order_id, order_type=None):
        """Delete the quote from the appropriate queue

        Find the quote, and delete it
        """
        (queue, i, j) = self.find_order(order_id, order_type)

        try:
            queue[i].delete_quote(order_id, j)
        finally:
            # Delete empty levels
            if len(queue[i].queue) == 0:
                del queue[i]

    def execute_trade(self, timestamp, volume, order_id, order_type=None):
        """Apply the effect of the execution on the book

        Make sure volume and ID are consistent with
        current order of book.
        Order sure be next in line on book, unless a price is specificed.
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
                    raise ExecutionPriorityExceptionList('LimitOrderBook:execute_trade',
                                                         errors_to_raise)
        except ExecutionPriorityException as e:
                if not self.skip_exception(e):
                    self.execution_errors_buffer.append(e)
                self.execute_trade_price(timestamp=timestamp,
                                         volume=volume, order_id=order_id)
        finally:
            # Delete empty levels
            if len(queue[0].queue) == 0:
                del queue[0]

    def skip_exception(self, e):
        """Indicate if the exception should be skipped."""
        return False

    def find_liquidity_maker(self, ask_id, bid_id):
        """Find which of the two orders is already on the book."""
        if not self.ask_order_on_book(ask_id):  # Sell order
            return bid_id
        elif not self.bid_order_on_book(bid_id):  # Buy order
            return ask_id
        else:
            raise Exception('LimitOrderBook:find_liquidity_maker',
                            'Could not determine maker/taker)')

    def execute_trade_price(self, timestamp, volume, order_id,
                            order_type=None):
        """Apply the effect of the execution on the book

        Make sure volume and ID are consistent with
        current order of book.
        Order sure be next in line on book, unless a price is specificed.
        """
        (queue, i, j) = self.find_order(order_id, order_type)

        queue[i].execute_trade_price(order_id, volume, timestamp)
        # Delete empty levels
        if len(queue[i].queue) == 0:
            del queue[i]

    def end_of_day(self):
        """Identify issues if this is the end of trading day."""
        # 1) Raise remaining exceptions.
        if len(self.execution_errors_buffer) > 0:
            raise ExecutionPriorityExceptionList('LimitOrderBook:execute_trade',
                                                 self.execution_errors_buffer)
