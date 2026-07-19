import pytest

from financial_charts.template.models import Currency, Money, Unit


def test_money_to_rescales_preserving_amount():
    price_in_agorot = Money(value=12345, currency=Currency.ILS, scale=Unit.ONES)
    price_in_millions = price_in_agorot.to(Unit.MILLIONS)

    assert price_in_millions.value == pytest.approx(12345 / 1_000_000)
    assert price_in_millions.currency == Currency.ILS


def test_money_add_same_currency_rescales_correctly():
    revenue_q1 = Money(value=1.5, currency=Currency.ILS, scale=Unit.MILLIONS)
    revenue_q2 = Money(value=500_000, currency=Currency.ILS, scale=Unit.ONES)

    total = revenue_q1 + revenue_q2

    assert total.scale == Unit.MILLIONS
    assert total.value == pytest.approx(2.0)


def test_money_add_different_currency_raises():
    usd_amount = Money(value=100, currency=Currency.USD, scale=Unit.ONES)
    ils_amount = Money(value=100, currency=Currency.ILS, scale=Unit.ONES)

    with pytest.raises(ValueError, match="different currencies"):
        usd_amount + ils_amount


def test_tase_agorot_price_converts_to_correct_shekel_value():
    # A known TASE price quote: 1523 agorot == 15.23 NIS.
    agorot_price = Money(value=1523, currency=Currency.ILS, scale=Unit.ONES)

    shekels = agorot_price.as_base_units() / 100

    assert shekels == pytest.approx(15.23)


def test_money_is_immutable():
    m = Money(value=1, currency=Currency.USD, scale=Unit.ONES)
    with pytest.raises(Exception):
        m.value = 2
