TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class ExecutionPriorityException(Exception):
    """An exception when market priority (price/time preference) is not respected."""

    pass


class VolumeInconsistencyException(Exception):
    """An exception when the volume of a trade or cancel is larger than the volume on the book."""

    pass


class OrderOnBook:
    """An order currently on the book.

    Just a low-level order structure for orders on the book. The order
    type and price  are irrelevant here, they depend on the queue and
    level the order belongs to.

    :param order_id:
    :type order_id: int
    :param timestamp:
    :type timestamp:
    :param volume:
    :type volume: int
    :param qualifs: qualifiers
    :type qualifs: dict or None
    """

    def __init__(self, order_id, timestamp, volume, qualifs=None):
        self.order_id = order_id
        self.timestamp = timestamp
        self.volume = volume
        self.qualifs = qualifs

    def print_out(self, indent=""):
        """
        Use this function to print information as a log.


        :param indent:
        :type indent: str
        :return: None
        """
        print(
            indent
            + str(self.volume)
            + " shares at "
            + str(self.timestamp)
            + " (id "
            + str(self.order_id)
            + ")"
        )

    def write_csv(self, file, timestamp, order_type, level, price, show_age):
        """
        This method is for writing the data to a csv file.

        :param file: output path
        :type file: str
        :param timestamp:
        :param order_type:
        :type order_type: str
        :param level:
        :type level: int
        :param price:
        :type price: int
        :param show_age:
        :type show_age: bool
        :return: None
        """
        if show_age:
            age = timestamp - self.timestamp
            file.write(
                (
                    str(timestamp)
                    + ","
                    + order_type
                    + ","
                    + str(level)
                    + ","
                    + str(price)
                    + ","
                    + str(self.order_id)
                    + ","
                    + str(self.volume)
                    + ","
                    + str(self.timestamp)
                    + ","
                    + str(age)
                    + "\n"
                ).encode()
            )
        else:
            file.write(
                (
                    str(timestamp)
                    + ","
                    + order_type
                    + ","
                    + str(level)
                    + ","
                    + str(price)
                    + ","
                    + str(self.order_id)
                    + ","
                    + str(self.volume)
                    + ","
                    + str(self.timestamp)
                    + "\n"
                ).encode()
            )


class Level:
    """
    This class ######## description ######

    :param price: related price for specific stock
    :type price: int
    :param queue: create a queue for orders
    :type queue: list
    """

    def __init__(self, price):
        self.price = price
        self.queue = []

    def order_factory(self, order_id, timestamp, volume, qualifs=None):
        """
        ########### description ############
        :param order_id:  a number for each order to make them clear
        :type order_id: int
        :param timestamp: time for orders
        :param volume: size of the order for trading
        :type volume: int
        :param qualifs: qualifiers
        :type qualifs: dict or None
        :return:
        """
        return OrderOnBook(
            order_id=order_id, timestamp=timestamp, volume=volume, qualifs=qualifs
        )

    def print_out(self, indent="", level=0):
        """

        :param indent:
        :param level:
        :return:
        """
        print(indent + "Price level " + str(level) + ": " + str(self.price))
        for x in self.queue:
            x.print_out(indent + "  ")

    def write_csv(
        self,
        file,
        timestamp,
        order_type,
        level,
        collapse_orders=False,
        price=None,
        show_age=False,
    ):
        """

        :param file:
        :param timestamp:
        :param order_type:
        :param level:
        :param collapse_orders:
        :param price:
        :param show_age:
        :return:
        """
        if price is None:
            price = self.price
        if collapse_orders:
            volume = 0
            n_orders = len(self.queue)
            for x in self.queue:
                volume += x.volume
            if show_age:
                vw_age = None
                age = None
                for x in self.queue:
                    order_age = timestamp - x.timestamp
                    if vw_age is None:
                        vw_age = order_age * x.volume
                    else:
                        vw_age += order_age * x.volume
                    if age is None:
                        age = order_age
                    else:
                        age += order_age
                vw_age = vw_age / float(volume)
                age = age / float(n_orders)
                first_age = timestamp - self.queue[0].timestamp
                last_age = timestamp - self.queue[-1].timestamp
                file.write(
                    (
                        str(timestamp)
                        + ","
                        + order_type
                        + ","
                        + str(level)
                        + ","
                        + str(price)
                        + ","
                        + str(volume)
                        + ","
                        + str(n_orders)
                        + ","
                        + str(vw_age)
                        + ","
                        + str(age)
                        + ","
                        + str(first_age)
                        + ","
                        + str(last_age)
                        + "\n"
                    ).encode()
                )
            else:
                file.write(
                    (
                        str(timestamp)
                        + ","
                        + order_type
                        + ","
                        + str(level)
                        + ","
                        + str(price)
                        + ","
                        + str(volume)
                        + ","
                        + str(n_orders)
                        + "\n"
                    ).encode()
                )
        else:
            for x in self.queue:
                x.write_csv(file, timestamp, order_type, level, self.price, show_age)

    def order_on_book(self, order_id):
        """
        Indicates if the order_id is on the books at the current level.

        :param order_id: a number for each order to make them clear
        :return:
        """
        for x in self.queue:
            if x.order_id == order_id:
                return True
        return False

    def volume(self):
        """
        Return the total volume for the order

        :return:
        """
        volume = 0
        for x in self.queue:
            volume += x.volume
        return volume

    def execution_price(self, volume):
        """
        Indicate the execution price for an order os size volume.

        Returns a tuple, with the first element being the total price and
        the second element the number of shares, which is
        min(requested volume, total book volume at current level)

        :param volume:
        :return:
        """
        volume_acc = 0

        for x in self.queue:
            volume_ord = x.volume
            volume_acc += volume_ord
            if volume_acc >= volume:
                volume_acc = volume
                break

        return (self.price * volume_acc, volume_acc)

    def find_order_on_book(self, order_id):
        """
        Find the order_id on the books at the current level.


        :param order_id:
        :return:
        """
        for x in range(len(self.queue)):
            if self.queue[x].order_id == order_id:
                return x
        return -1

    def cancel_quote(self, order_id, volume, i=None):
        """
        Cancel order with order_id and volume. Returns true on success,
            false if not in this level


        :param order_id:
        :param volume:
        :param i:
        :return:
        """
        # Find the quote, and delete it (make sure volumes match)
        if i is None:
            i = self.find_order_on_book(order_id)
            if i == -1:
                raise Exception(
                    "Level:cancel_quote", "Order ID " + str(order_id) + " not on level"
                )
        # Check for consistency in volume
        if self.queue[i].volume < volume:
            book_vol = self.queue[i].volume
            del self.queue[i]
            raise VolumeInconsistencyException(
                "Level:cancel_quote",
                "Cancel volume ("
                + str(volume)
                + ") larger than book volume ("
                + str(book_vol)
                + ") for order ID "
                + str(order_id),
                order_id,
            )
        # Delete order
        elif self.queue[i].volume == volume:
            del self.queue[i]
        else:
            self.queue[i].volume -= volume

    def delete_quote(self, order_id, i=None):
        """
        Delete order with order_id . Returns true on success,
            false if not in this level

        :param order_id:
        :param i:
        :return:
        """
        if i is None:
            i = self.find_order_on_book(order_id)
            if i == -1:
                raise Exception(
                    "Level:delete_quote", "Order ID " + str(order_id) + " not on level"
                )

        # Delete order
        del self.queue[i]
        return True

    def enter_quote(self, timestamp, volume, order_id, qualifs=None):
        """
        Enter the quote at the back of the queue.

        :param timestamp:
        :param volume:
        :param order_id:
        :param qualifs: qualifiers
        :type qualifs: dict or None
        :return:
        """
        self.queue.append(self.order_factory(order_id, timestamp, volume, qualifs))

    def enter_quote_out_of_order(self, timestamp, volume, order_id, qualifs=None):
        """
        Enter the quote in the queue according to timestamp.


        :param timestamp:
        :param volume:
        :param order_id:
        :param qualifs: qualifiers
        :type qualifs: dict or None
        :return:
        """
        i = 0
        for x in self.queue:
            if x.timestamp < timestamp:
                i = i + 1
            else:
                continue

        self.queue.insert(i, self.order_factory(order_id, timestamp, volume, qualifs))

    def enter_quote_at_position(
        self, timestamp, volume, order_id, position, check_position, qualifs=None
    ):
        """
        Enter the quote in the queue according to  stated position.


        :param timestamp:
        :param volume:
        :param order_id:
        :param position:
        :param check_position:
        :param qualifs: qualifiers
        :type qualifs: dict or None
        :return:
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
                "Order ID "
                + str(order_id)
                + " should be at position "
                + str(i)
                + ", not "
                + str(position - 1)
                + ".",
                timestamp,
                order_id,
                None,
            )

    def execute_trade(self, order_id, volume, timestamp=None):
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
                "Order ID "
                + str(order_id)
                + " not first in line, "
                + str(self.queue[0].order_id)
                + " is.",
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
                "Volume ("
                + str(volume)
                + ") larger than book volume ("
                + str(book_vol)
                + ") for order "
                + str(order_id),
                order_id,
            )

    def execute_trade_price(self, order_id, volume, timestamp=None):
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
            raise Exception(
                "Level:execute_trade_price",
                "Order ID " + str(order_id) + " not in queue",
            )
        if self.queue[order].volume > volume:
            self.queue[order].volume -= volume
        elif self.queue[order].volume == volume:
            del self.queue[order]
        else:
            book_vol = str(self.queue[order].volume)
            del self.queue[order]
            raise VolumeInconsistencyException(
                "Level:execute_trade_price",
                "Volume ("
                + str(volume)
                + ") larger than book volume ("
                + str(book_vol)
                + ")",
                order_id,
            )
