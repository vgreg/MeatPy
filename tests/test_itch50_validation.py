"""Tests for ITCH 5.0 message validation methods."""

import struct

from src.meatpy.itch50.itch50_market_message import (
    CrossTradeMessage,
    ITCH50MarketMessage,
    MarketParticipantPositionMessage,
    NoiiMessage,
    RpiiMessage,
    StockDirectoryMessage,
    StockTradingActionMessage,
    SystemEventMessage,
)


class TestITCH50Validation:
    """Test validation methods for ITCH 5.0 messages."""

    def test_validate_code_method(self):
        """Test the base validate_code method."""
        test_dict = {b"A": "Valid A", b"B": "Valid B", b"C": "Valid C"}

        assert ITCH50MarketMessage.validate_code(b"A", test_dict) is True
        assert ITCH50MarketMessage.validate_code(b"B", test_dict) is True
        assert ITCH50MarketMessage.validate_code(b"C", test_dict) is True
        assert ITCH50MarketMessage.validate_code(b"D", test_dict) is False
        assert ITCH50MarketMessage.validate_code(b"", test_dict) is False

    def test_get_code_description_method(self):
        """Test the get_code_description method."""
        test_dict = {b"A": "Valid A", b"B": "Valid B", b"C": "Valid C"}

        assert ITCH50MarketMessage.get_code_description(b"A", test_dict) == "Valid A"
        assert ITCH50MarketMessage.get_code_description(b"B", test_dict) == "Valid B"
        assert ITCH50MarketMessage.get_code_description(b"C", test_dict) == "Valid C"
        assert ITCH50MarketMessage.get_code_description(b"D", test_dict) == "Unknown"

    def test_validate_system_event_code(self):
        """Test system event code validation."""
        valid_codes = [b"O", b"S", b"Q", b"M", b"E", b"C"]
        invalid_codes = [b"X", b"Y", b"Z", b"1", b""]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_system_event_code(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_system_event_code(code) is False

    def test_validate_market_code(self):
        """Test market code validation."""
        valid_codes = [b"N", b"A", b"P", b"Q", b"G", b"S", b"Z", b"V", b" "]
        invalid_codes = [b"X", b"Y", b"1", b"2", b""]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_market_code(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_market_code(code) is False

    def test_validate_financial_status_indicator(self):
        """Test financial status indicator validation."""
        valid_codes = [b"D", b"E", b"Q", b"S", b"G", b"H", b"J", b"K", b"C", b"N", b" "]
        invalid_codes = [b"X", b"Y", b"1", b"2", b""]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_financial_status_indicator(code) is True

        for code in invalid_codes:
            assert (
                ITCH50MarketMessage.validate_financial_status_indicator(code) is False
            )

    def test_validate_trading_state(self):
        """Test trading state validation."""
        valid_codes = [b"H", b"P", b"Q", b"T"]
        invalid_codes = [b"X", b"Y", b"1", b"2", b"", b" "]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_trading_state(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_trading_state(code) is False

    def test_validate_market_maker_mode(self):
        """Test market maker mode validation."""
        valid_codes = [b"N", b"P", b"S", b"R", b"L"]
        invalid_codes = [b"X", b"Y", b"1", b"2", b"", b" "]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_market_maker_mode(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_market_maker_mode(code) is False

    def test_validate_market_participant_state(self):
        """Test market participant state validation."""
        valid_codes = [b"A", b"E", b"W", b"S", b"D"]
        invalid_codes = [b"X", b"Y", b"1", b"2", b"", b" "]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_market_participant_state(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_market_participant_state(code) is False

    def test_validate_interest_description(self):
        """Test interest description validation."""
        valid_codes = [b"B", b"S", b"A", b"N"]
        invalid_codes = [b"X", b"Y", b"1", b"2", b"", b" "]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_interest_description(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_interest_description(code) is False

    def test_validate_cross_type(self):
        """Test cross type validation."""
        valid_codes = [b"O", b"C", b"H", b"I"]
        invalid_codes = [b"X", b"Y", b"1", b"2", b"", b" "]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_cross_type(code) is True

        for code in invalid_codes:
            assert ITCH50MarketMessage.validate_cross_type(code) is False


class TestSystemEventMessageValidation:
    """Test SystemEventMessage validation."""

    def test_valid_system_event_message(self):
        """Test validation of valid SystemEventMessage."""
        binary_data = b"S" + struct.pack("!HHHIc", 1, 2, 3, 4, b"O")
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, SystemEventMessage)
        assert message.validate() is True

    def test_invalid_system_event_message(self):
        """Test validation of invalid SystemEventMessage."""
        message = SystemEventMessage()
        message.code = b"X"  # Invalid code

        assert message.validate() is False

    def test_all_valid_system_event_codes(self):
        """Test all valid system event codes."""
        valid_codes = [b"O", b"S", b"Q", b"M", b"E", b"C"]

        for code in valid_codes:
            message = SystemEventMessage()
            message.code = code
            assert message.validate() is True


class TestStockDirectoryMessageValidation:
    """Test StockDirectoryMessage validation."""

    def test_valid_stock_directory_message(self):
        """Test validation of valid StockDirectoryMessage."""
        args = [
            1,  # stock_locate
            2,  # tracking_number
            3,  # ts1
            4,  # ts2
            b"AAPL    ",  # stock
            b"Q",  # category (valid market code)
            b"N",  # status (valid financial status)
            100,  # lotsize
            b"Y",  # lotsonly (valid round lots code)
            b"Q",  # issue_class
            b"  ",  # issue_sub
            b"Y",  # authenticity
            b"Y",  # shortsale_thresh
            b"N",  # ipo_flag
            b"1",  # luld_ref
            b"N",  # etp_flag
            2,  # etp_leverage
            b" ",  # inverse_ind
        ]
        packed = struct.pack("!HHHI8sccIcc2scccccIc", *args)
        binary_data = b"R" + packed
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, StockDirectoryMessage)
        assert message.validate() is True

    def test_invalid_stock_directory_message_category(self):
        """Test validation with invalid category."""
        message = StockDirectoryMessage()
        message.category = b"X"  # Invalid market code
        message.status = b"N"  # Valid financial status
        message.lotsonly = b"Y"  # Valid round lots code

        assert message.validate() is False

    def test_invalid_stock_directory_message_status(self):
        """Test validation with invalid status."""
        message = StockDirectoryMessage()
        message.category = b"Q"  # Valid market code
        message.status = b"X"  # Invalid financial status
        message.lotsonly = b"Y"  # Valid round lots code

        assert message.validate() is False

    def test_invalid_stock_directory_message_lotsonly(self):
        """Test validation with invalid lotsonly."""
        message = StockDirectoryMessage()
        message.category = b"Q"  # Valid market code
        message.status = b"N"  # Valid financial status
        message.lotsonly = b"X"  # Invalid round lots code

        assert message.validate() is False


class TestStockTradingActionMessageValidation:
    """Test StockTradingActionMessage validation."""

    def test_valid_stock_trading_action_message(self):
        """Test validation of valid StockTradingActionMessage."""
        binary_data = b"H" + struct.pack(
            "!HHHI8scc4s", 1, 2, 3, 4, b"AAPL    ", b"T", b" ", b"    "
        )
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, StockTradingActionMessage)
        assert message.validate() is True

    def test_invalid_stock_trading_action_message(self):
        """Test validation of invalid StockTradingActionMessage."""
        message = StockTradingActionMessage()
        message.state = b"X"  # Invalid trading state

        assert message.validate() is False

    def test_all_valid_trading_states(self):
        """Test all valid trading states."""
        valid_states = [b"H", b"P", b"Q", b"T"]

        for state in valid_states:
            message = StockTradingActionMessage()
            message.state = state
            assert message.validate() is True


class TestMarketParticipantPositionMessageValidation:
    """Test MarketParticipantPositionMessage validation."""

    def test_valid_market_participant_position_message(self):
        """Test validation of valid MarketParticipantPositionMessage."""
        binary_data = b"L" + struct.pack(
            "!HHHI4s8sccc", 1, 2, 3, 4, b"MPID", b"AAPL    ", b"Y", b"N", b"A"
        )
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, MarketParticipantPositionMessage)
        assert message.validate() is True

    def test_invalid_market_participant_position_message_primary_mm(self):
        """Test validation with invalid primary market maker."""
        message = MarketParticipantPositionMessage()
        message.primary_market_maker = b"X"  # Invalid primary market maker
        message.market_maker_mode = b"N"  # Valid market maker mode
        message.state = b"A"  # Valid participant state

        assert message.validate() is False

    def test_invalid_market_participant_position_message_mm_mode(self):
        """Test validation with invalid market maker mode."""
        message = MarketParticipantPositionMessage()
        message.primary_market_maker = b"Y"  # Valid primary market maker
        message.market_maker_mode = b"X"  # Invalid market maker mode
        message.state = b"A"  # Valid participant state

        assert message.validate() is False

    def test_invalid_market_participant_position_message_state(self):
        """Test validation with invalid participant state."""
        message = MarketParticipantPositionMessage()
        message.primary_market_maker = b"Y"  # Valid primary market maker
        message.market_maker_mode = b"N"  # Valid market maker mode
        message.state = b"X"  # Invalid participant state

        assert message.validate() is False


class TestCrossTradeMessageValidation:
    """Test CrossTradeMessage validation."""

    def test_valid_cross_trade_message(self):
        """Test validation of valid CrossTradeMessage."""
        binary_data = b"Q" + struct.pack(
            "!HHHIQ8sIQc", 1, 2, 3, 4, 100, b"AAPL    ", 5000, 123456, b"O"
        )
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, CrossTradeMessage)
        assert message.validate() is True

    def test_invalid_cross_trade_message(self):
        """Test validation of invalid CrossTradeMessage."""
        message = CrossTradeMessage()
        message.crossType = b"X"  # Invalid cross type

        assert message.validate() is False

    def test_all_valid_cross_types(self):
        """Test all valid cross types."""
        valid_types = [b"O", b"C", b"H", b"I"]

        for cross_type in valid_types:
            message = CrossTradeMessage()
            message.crossType = cross_type
            assert message.validate() is True


class TestNoiiMessageValidation:
    """Test NoiiMessage validation."""

    def test_valid_noii_message(self):
        """Test validation of valid NoiiMessage."""
        binary_data = b"I" + struct.pack(
            "!HHHIQQc8sIIIcc",
            1,
            2,
            3,
            4,
            100,
            50,
            b"B",
            b"AAPL    ",
            5000,
            5100,
            5050,
            b"O",
            b"L",
        )
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, NoiiMessage)
        assert message.validate() is True

    def test_invalid_noii_message(self):
        """Test validation of invalid NoiiMessage."""
        message = NoiiMessage()
        message.crossType = b"X"  # Invalid cross type

        assert message.validate() is False


class TestRpiiMessageValidation:
    """Test RpiiMessage validation."""

    def test_valid_rpii_message(self):
        """Test validation of valid RpiiMessage."""
        binary_data = b"N" + struct.pack("!HHHI8sc", 1, 2, 3, 4, b"AAPL    ", b"B")
        message = ITCH50MarketMessage.from_bytes(binary_data)

        assert isinstance(message, RpiiMessage)
        assert message.validate() is True

    def test_invalid_rpii_message(self):
        """Test validation of invalid RpiiMessage."""
        message = RpiiMessage()
        message.interest = b"X"  # Invalid interest code

        assert message.validate() is False

    def test_all_valid_interest_codes(self):
        """Test all valid interest codes."""
        valid_codes = [b"B", b"S", b"A", b"N"]

        for code in valid_codes:
            message = RpiiMessage()
            message.interest = code
            assert message.validate() is True


class TestBaseMessageValidation:
    """Test base message validation."""

    def test_base_message_validate_returns_true(self):
        """Test that base message validate method returns True."""
        message = ITCH50MarketMessage()
        assert message.validate() is True


class TestValidationWithFixedTypos:
    """Test that the fixed typos are correctly handled in validation."""

    def test_corrected_financial_status_descriptions(self):
        """Test that corrected descriptions are available."""
        # Test the corrected spellings
        assert (
            ITCH50MarketMessage.get_code_description(
                b"E", ITCH50MarketMessage.finStatusbsindicators
            )
            == "Delinquent"
        )
        assert (
            ITCH50MarketMessage.get_code_description(
                b"H", ITCH50MarketMessage.finStatusbsindicators
            )
            == "Deficient and Delinquent"
        )
        assert (
            ITCH50MarketMessage.get_code_description(
                b"J", ITCH50MarketMessage.finStatusbsindicators
            )
            == "Delinquent and Bankrupt"
        )
        assert (
            ITCH50MarketMessage.get_code_description(
                b"N", ITCH50MarketMessage.finStatusbsindicators
            )
            == "Normal (Default): Issuer Is NOT Deficient, Delinquent, or Bankrupt"
        )

    def test_financial_status_validation_still_works(self):
        """Test that validation still works after typo fixes."""
        valid_codes = [b"D", b"E", b"Q", b"S", b"G", b"H", b"J", b"K", b"C", b"N", b" "]

        for code in valid_codes:
            assert ITCH50MarketMessage.validate_financial_status_indicator(code) is True
