from onfido.data import check_supported_country, get_countries


def test_check_supported_country_matches_json():
    test_params = (
        (
            "YEM",
            False,
        ),
        (
            "ZMB",
            True,
        ),
        (
            "IND",
            True,
        ),
        (
            "ERI",
            False,
        ),
    )

    data = get_countries()
    assert len(data) == 249

    for test in test_params:
        assert check_supported_country(test[0]) == test[1]
