from collector.deals import discount, passes


def test_discount_from_reference_and_percent():
    assert discount("LG 32in OLED Monitor $599 (Reg. $1199)") == (50.0, 600.0)
    assert discount("Samsung 990 Pro 4TB SSD $249.99 45% off")[0] == 45.0
    assert discount("Logitech Mouse $49") == (None, None)


def test_user_bar_40pct_or_big_saving():
    assert passes("RTX 5090 $1599 was $2099", 40, 300)          # 24% but saves $500
    assert passes("Monitor $299 (Reg. $599)", 40, 300)           # 50%
    assert not passes("Keyboard $89 (List $119)", 40, 300)      # 25%, $30
    assert not passes("Headphones $199", 40, 300)               # no reference price
