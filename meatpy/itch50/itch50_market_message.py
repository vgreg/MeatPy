import struct

from ..message_parser import MarketMessage

class ITCH50MarketMessage(MarketMessage):
    """A market message in ITCH 4.1 format.
    Updated to ITCH 5.0 format.

class ITCH50MarketMessage(MarketMessage):
    """A market message in ITCH 4.1 format."""

    sysEventCodes = {
        b"O": "Start of Messages",
        b"S": "Start of System Hours",
        b"Q": "Start of Market Hours",
        b"M": "End of Market Hours",
        b"E": "End of System Hours",
        b"C": "End of Messages",
    }

    market = {
        b"N": "NYSE",
        b"A": "AMEX",
        b"P": "Arca",
        b"Q": "NASDAQ Global Select",
        b"G": "NASDAQ Global Market",
        b"S": "NASDAQ Capital Market",
        b"Z": "BATS",
        b"V": "Investors’ Exchange",
        b" ": "Not available",
    }

    finStatusbsindicators = {
        b"D": "Deficient",
        b"E": "Deliquent",
        b"Q": "Bankrupt",
        b"S": "Suspended",
        b"G": "Deficient and Bankrupt",
        b"H": "Deficient and Deliquent",
        b"J": "Delinquent and Bankrput",
        b"K": "Deficient, Delinquent and Bankrupt",
        b"C": "Creations and/or Redemptions Suspended for Exchange Traded Product",
        b"N": "Normal (Defualt): Issuer Is NOT Deficient, Delinquent, or Bankrupt",
        b" ": "Not available. Firms should refer to SIAC feeds for code if needed",
    }

    roundLotsOnly = {b"Y": "Only round lots", b"N": "Odd and Mixed lots"}

    # These list get overriden in individual messages... still relevant?

    tradingStates = {
        b"H": "Halted across all U.S. equity markets / SROs",
        b"P": "Paused across all U.S. equity markets / SROs",
        b"Q": "Quotation only period for cross-SRO halt or pause",
        b"T": "Trading on NASDAQ",
    }

    primaryMarketMaker = {
        b"Y": "Primary market maker",
        b"N": "Non-primary market maker",
    }

    marketMakerModes = {
        b"N": "Normal",
        b"P": "Passive",
        b"S": "Syndicate",
        b"R": "Pre-syndicate",
        b"L": "Penalty",
    }

    marketParticipantStates = {
        b"A": "Active",
        b"E": "Excused",
        b"W": "Withdrawn",
        b"S": "Suspended",
        b"D": "Deleted",
    }

    interest = {
        b"B": "RPI orders avail on buy side",
        b"S": "RPI orders avail on sell side",
        b"A": "RPI orders avail on both sides",
        b"N": "No RPI orders avail",
    }

    crossType = {
        b"O": "NASDAQ Opening Cross",
        b"C": "NASDAQ Closing Cross",
        b"H": "Cross for IPO and Halted Securities",
        b"I": "NASDAQ Cross Network: Intraday Cross and Post-Close Cross",
    }

    def print_out(self, indent):
        print(indent + self.description)

    def set_timestamp(self, ts1, ts2):
        self.timestamp = ts2 | (ts1 << 32)

    def split_timestamp(self):
        ts1 = self.timestamp >> 32
        ts2 = self.timestamp - (ts1 << 32)
        return (ts1, ts2)


class SystemEventMessage(ITCH50MarketMessage):
    type = b"S"
    description = "System Event Message"
    message_size = struct.calcsize("!HHHIc") + 1

    def __init__(self, message):
        (self.stock_locate, self.tracking_number, ts1, ts2, self.code) = struct.unpack(
            "!HHHIc", message[1:]
        )
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.code,
        )


class StockDirectoryMessage(ITCH50MarketMessage):
    type = b"R"
    description = "Stock Directory Message"
    message_size = struct.calcsize("!HHHI8sccIcc2scccccIc") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.category,
            self.status,
            self.lotsize,
            self.lotsonly,
            self.issue_class,
            self.issue_sub,
            self.authenticity,
            self.shortsale_thresh,
            self.ipo_flag,
            self.luld_ref,
            self.etp_flag,
            self.etp_leverage,
            self.inverse_ind,
        ) = struct.unpack("!HHHI8sccIcc2scccccIc", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sccIcc2scccccIc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.category,
            self.status,
            self.lotsize,
            self.lotsonly,
            self.issue_class,
            self.issue_sub,
            self.authenticity,
            self.shortsale_thresh,
            self.ipo_flag,
            self.luld_ref,
            self.etp_flag,
            self.etp_leverage,
            self.inverse_ind,
        )


class StockTradingActionMessage(ITCH50MarketMessage):
    type = b"H"
    description = "Stock Trading Message"
    message_size = struct.calcsize("!HHHI8scc4s") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.state,
            self.reserved,
            self.reason,
        ) = struct.unpack("!HHHI8scc4s", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8scc4s",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.state,
            self.reserved,
            self.reason,
        )


class RegSHOMessage(ITCH50MarketMessage):
    type = b"Y"
    description = "Reg SHO Short Sale Message"
    message_size = struct.calcsize("!HHHI8sc") + 1

    def __init__(self, message):
        (self.stock_locate, self.tracking_number, ts1, ts2, self.stock, self.action) = (
            struct.unpack("!HHHI8sc", message[1:])
        )
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.action,
        )


class MarketParticipantPositionMessage(ITCH50MarketMessage):
    type = b"L"
    description = "Market Participant Message"
    message_size = struct.calcsize("!HHHI4s8sccc") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.mpid,
            self.stock,
            self.primaryMarketMaker,
            self.marketMakermode,
            self.state,
        ) = struct.unpack("!HHHI4s8sccc", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI4s8sccc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.mpid,
            self.stock,
            self.primaryMarketMaker,
            self.marketMakermode,
            self.state,
        )


class AddOrderMessage(ITCH50MarketMessage):
    type = b"A"
    description = "Add Order Message"
    message_size = struct.calcsize("!HHHIQcI8sI") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
        ) = struct.unpack("!HHHIQcI8sI", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQcI8sI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
        )


class AddOrderMPIDMessage(ITCH50MarketMessage):
    type = b"F"
    description = "Add Order w/ MPID Message"
    message_size = struct.calcsize("!HHHIQcI8sI4s") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
            self.attribution,
        ) = struct.unpack("!HHHIQcI8sI4s", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQcI8sI4s",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
            self.attribution,
        )


class OrderExecutedMessage(ITCH50MarketMessage):
    type = b"E"
    description = "Order Executed Message"
    message_size = struct.calcsize("!HHHIQIQ") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.shares,
            self.match,
        ) = struct.unpack("!HHHIQIQ", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.shares,
            self.match,
        )


class OrderExecutedPriceMessage(ITCH50MarketMessage):
    type = b"C"
    description = "Order Executed w/ Price Message"
    message_size = struct.calcsize("!HHHIQIQcI") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.shares,
            self.match,
            self.printable,
            self.price,
        ) = struct.unpack("!HHHIQIQcI", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQIQcI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.shares,
            self.match,
            self.printable,
            self.price,
        )


class OrderCancelMessage(ITCH50MarketMessage):
    type = b"X"
    description = "Order Cancel Message"
    message_size = struct.calcsize("!HHHIQI") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.cancelShares,
        ) = struct.unpack("!HHHIQI", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.cancelShares,
        )


class OrderDeleteMessage(ITCH50MarketMessage):
    type = b"D"
    description = "Order Delete Message"
    message_size = struct.calcsize("!HHHIQ") + 1

    def __init__(self, message):
        (self.stock_locate, self.tracking_number, ts1, ts2, self.orderRefNum) = (
            struct.unpack("!HHHIQ", message[1:])
        )
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
        )


class OrderReplaceMessage(ITCH50MarketMessage):
    type = b"U"
    description = "Order Replaced Message"
    message_size = struct.calcsize("!HHHIQQII") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.origOrderRefNum,
            self.newOrderRefNum,
            self.shares,
            self.price,
        ) = struct.unpack("!HHHIQQII", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQQII",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.origOrderRefNum,
            self.newOrderRefNum,
            self.shares,
            self.price,
        )


class TradeMessage(ITCH50MarketMessage):
    type = b"P"
    description = "Trade Message"
    message_size = struct.calcsize("!HHHIQcI8sIQ") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
            self.match,
        ) = struct.unpack("!HHHIQcI8sIQ", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQcI8sIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.orderRefNum,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
            self.match,
        )


class CrossTradeMessage(ITCH50MarketMessage):
    type = b"Q"
    description = "Cross Trade Message"
    message_size = struct.calcsize("!HHHIQ8sIQc") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.shares,
            self.stock,
            self.price,
            self.match,
            self.crossType,
        ) = struct.unpack("!HHHIQ8sIQc", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQ8sIQc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.shares,
            self.stock,
            self.price,
            self.match,
            self.crossType,
        )


class BrokenTradeMessage(ITCH50MarketMessage):
    type = b"B"
    description = "Broken Trade Message"
    message_size = struct.calcsize("!HHHIQ") + 1

    def __init__(self, message):
        (self.stock_locate, self.tracking_number, ts1, ts2, self.match) = struct.unpack(
            "!HHHIQ", message[1:]
        )
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.match,
        )


class NoiiMessage(ITCH50MarketMessage):
    type = b"I"
    description = "NOII Message"
    message_size = struct.calcsize("!HHHIQQc8sIIIcc") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.pairedShares,
            self.imbalance,
            self.imbalanceDirection,
            self.stock,
            self.farPrice,
            self.nearPrice,
            self.currentRefPrice,
            self.crossType,
            self.priceVariationbsindicator,
        ) = struct.unpack("!HHHIQQc8sIIIcc", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQQc8sIIIcc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.pairedShares,
            self.imbalance,
            self.imbalanceDirection,
            self.stock,
            self.farPrice,
            self.nearPrice,
            self.currentRefPrice,
            self.crossType,
            self.priceVariationbsindicator,
        )


class RpiiMessage(ITCH50MarketMessage):
    type = b"N"
    description = "Retail Price Improvement Message"
    message_size = struct.calcsize("!HHHI8sc") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.interest,
        ) = struct.unpack("!HHHI8sc", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.interest,
        )


class MWCBDeclineLevelMessage(ITCH50MarketMessage):
    type = b"V"
    description = "MWCB Decline Level Message"
    message_size = struct.calcsize("!HHHIQQQ") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.level1,
            self.level2,
            self.level3,
        ) = struct.unpack("!HHHIQQQ", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQQQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.level1,
            self.level2,
            self.level3,
        )


class MWCBBreachMessage(ITCH50MarketMessage):
    type = b"W"
    description = "MWCB Breach Message"
    message_size = struct.calcsize("!HHHIc") + 1

    def __init__(self, message):
        (self.stock_locate, self.tracking_number, ts1, ts2, self.breached_level) = (
            struct.unpack("!HHHIc", message[1:])
        )
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.breached_level,
        )


class IPOQuotingPeriodUpdateMessage(ITCH50MarketMessage):
    type = b'k'
    description = "Retail Price Improvement Message"
    message_size = struct.calcsize("!HHHI8sIcI") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.ipo_quotation_release_time,
            self.ipo_quotation_release_qualifier,
            self.ipo_price,
        ) = struct.unpack("!HHHI8sIcI", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sIcI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.ipo_quotation_release_time,
            self.ipo_quotation_release_qualifier,
            self.ipo_price,
        )


class LULDAuctionCollarMessage(ITCH50MarketMessage):
    type = b"J"
    description = "LULD Auction Collar Message"
    message_size = struct.calcsize("!HHHI8sIIII") + 1

    def __init__(self, message):
        (
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.auction_collar_reference_price,
            self.upper_auction_collar_price,
            self.lower_auction_collar_price,
            self.auction_collar_extension,
        ) = struct.unpack("!HHHI8sIIII", message[1:])
        self.set_timestamp(ts1, ts2)

    def pack(self):
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sIIII",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.auction_collar_reference_price,
            self.upper_auction_collar_price,
            self.lower_auction_collar_price,
            self.auction_collar_extension,
        )


class OperationalHaltMessage(ITCH50MarketMessage):
    type = b"h"
    description = "Operational Halt Message"
    message_size = struct.calcsize("!HHHI8scc") + 1 

    def __init__(self, message):
        (self.stock_locate,
         self.tracking_number,
         ts1,
         ts2,
         self.stock,
         self.market_code,
         self.halt_action) = struct.unpack("!HHHI8scc", message[1:])

        self.set_timestamp(ts1, ts2)

    def pack(self):
        ts1, ts2 = self.split_timestamp()
        return struct.pack("!cHHHI8scc",
                           self.type,
                           self.stock_locate,
                           self.tracking_number,
                           ts1,
                           ts2,
                           self.stock,
                           self.market_code,
                           self.halt_action)
    
    
class DirectListingCapitalRaiseMessage(ITCH50MarketMessage):
    type = b'O'
    description = "Direct Listing with Capital Raise (DLCR) Message"
    message_size = struct.calcsize("!HHHI8scIIIIQII") + 1  # +1 for message type byte

    def __init__(self, message):
        (self.stock_locate,
         self.tracking_number,
         ts1,
         ts2,
         self.stock,
         self.open_eligibility_status,
         self.min_allowable_price,
         self.max_allowable_price,
         self.near_execution_price,
         self.near_execution_time,
         self.lower_price_range_collar,
         self.upper_price_range_collar) = struct.unpack("!HHHI8scIIIIQII", message[1:])

        self.set_timestamp(ts1, ts2)

    def pack(self):
        ts1, ts2 = self.split_timestamp()
        return struct.pack("!cHHHI8scIIIIQII",
                           self.type,
                           self.stock_locate,
                           self.tracking_number,
                           ts1,
                           ts2,
                           self.stock,
                           self.open_eligibility_status,
                           self.min_allowable_price,
                           self.max_allowable_price,
                           self.near_execution_price,
                           self.near_execution_time,
                           self.lower_price_range_collar,
                           self.upper_price_range_collar)
