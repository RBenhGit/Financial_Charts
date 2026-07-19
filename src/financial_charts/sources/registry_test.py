from unittest.mock import patch

import pytest

from financial_charts.sources.base import MissingCredentials
from financial_charts.sources.registry import get_source
from financial_charts.sources.twelvedata.adapter import TwelveDataAdapter
from financial_charts.sources.yfinance.adapter import YFinanceAdapter


def test_resolves_yfinance():
    assert isinstance(get_source("yfinance"), YFinanceAdapter)


def test_resolves_twelvedata_with_credentials():
    with patch.dict("os.environ", {"TWELVEDATA_API_KEY": "test-key"}):
        assert isinstance(get_source("twelvedata"), TwelveDataAdapter)


def test_twelvedata_without_credentials_raises_missing_credentials():
    with (
        patch("financial_charts.sources.twelvedata.adapter.load_dotenv"),
        patch.dict("os.environ", {}, clear=True),
    ):
        with pytest.raises(MissingCredentials):
            get_source("twelvedata")


def test_unknown_source_raises_key_error():
    with pytest.raises(KeyError):
        get_source("not-a-real-source")
