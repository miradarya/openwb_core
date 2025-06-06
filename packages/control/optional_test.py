from unittest.mock import Mock
from control.optional import Optional


def test_et_get_loading_hours(monkeypatch):
    # setup
    opt = Optional()
    opt.data.et.get.prices = PRICE_LIST
    mock_et_provider_available = Mock(return_value=True)
    monkeypatch.setattr(opt, "_et_provider_available", mock_et_provider_available)

    # execution
    loading_hours = opt.et_get_loading_hours(3600, 7200)

    # evaluation
    assert loading_hours == [1698231600]


PRICE_LIST = {"1698224400": 0.00012499,
              "1698228000": 0.00011737999999999999,
              "1698231600": 0.00011562000000000001,
              "1698235200": 0.00012447,
              "1698238800": 0.00013813,
              "1698242400": 0.00014751,
              "1698246000": 0.00015372999999999998,
              "1698249600": 0.00015462,
              "1698253200": 0.00015771,
              "1698256800": 0.00013708,
              "1698260400": 0.00012355,
              "1698264000": 0.00012006,
              "1698267600": 0.00011279999999999999}
