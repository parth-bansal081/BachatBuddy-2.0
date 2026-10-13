from bb.normalize import merchant_key


def test_upi_slash_formats_collapse_to_one_key():
    a = merchant_key("UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment")
    b = merchant_key("UPI/DR/998877665544/SWIGGY/HDFC/swiggy@okaxis/Order 12345")
    assert a == b == "swiggy"


def test_upi_dash_format_matches_slash_format():
    assert merchant_key("UPI-SWIGGY-swiggy@ybl-YESB0000262-412345678901-UPI") == "swiggy"


def test_multiword_merchant_is_kept():
    assert merchant_key("UPI/DR/412345678901/DOMINOS PIZZA/ICIC/dominos@ibl/Payment") == "dominos pizza"


def test_person_name_is_kept():
    assert merchant_key("UPI-RAHUL SHARMA-rahul@ybl-SBIN0001234-412345678901-UPI") == "rahul sharma"


def test_neft_salary_drops_reference_numbers():
    a = merchant_key("NEFT-HDFCN52026101012345-ACME TECH PVT LTD-SALARY")
    b = merchant_key("NEFT-HDFCN52026110198765-ACME TECH PVT LTD-SALARY")
    assert a == b
    assert "acme" in a


def test_pos_masked_card_removed():
    assert merchant_key("POS 4321XXXXXX1234 AMAZON BANGALORE") == "amazon bangalore"


def test_short_numbers_inside_names_are_kept():
    assert "7" in merchant_key("UPI/DR/412345678901/7 ELEVEN/YESB/seven@ybl/Payment")


def test_empty_and_noise_only():
    assert merchant_key("") == ""
    assert merchant_key("   ") == ""
    assert merchant_key("UPI/DR/412345678901") == ""
