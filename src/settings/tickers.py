# Panel A: Cross-asset universe
PANEL_A = [
    # Equity
    "SPY",  # SPDR S&P 500 ETF Trust - US large-cap equities

    # Fixed income
    "SHY",  # iShares 1-3 Year Treasury Bond ETF - short-term US Treasuries
    "TLT",  # iShares 20+ Year Treasury Bond ETF - long-term US Treasuries
    "AGG",  # iShares Core US Aggregate Bond ETF - broad US investment-grade bonds
    "HYG",  # iShares iBoxx High Yield Corporate Bond ETF - US high-yield credit

    # Commodities
    "GLD",  # SPDR Gold Shares - physical gold exposure
    "DBC",  # Invesco DB Commodity Index Tracking Fund - broad commodities
    "USO",  # United States Oil Fund - crude oil exposure

    # Currencies
    # "UUP"  # US dollar index ETF

    # Real estate
    "VNQ",  # Vanguard Real Estate ETF - US real estate investment trusts
]


# Panel B: International equity universe
PANEL_B = [
    "SPY",  # SPDR S&P 500 ETF Trust - United States benchmark
    "EFA",  # iShares MSCI EAFE ETF - broad developed ex-US equities
    "EEM",  # iShares MSCI Emerging Markets ETF - emerging-market equities
    "EWG",  # iShares MSCI Germany ETF - German equities
    "EWU",  # iShares MSCI United Kingdom ETF - United Kingdom equities
    "EWJ",  # iShares MSCI Japan ETF - Japanese equities
]


# Canonical ETF universe: the union of Panel A and Panel B (SPY is shared, so it
# appears once). Order follows Panel A, then the Panel B additions. The two
# panels are analysed separately; this union is the "etf_assets" universe and the
# column set of the labeled return table built in scripts/06.
ETF_ASSETS = list(dict.fromkeys(PANEL_A + PANEL_B))
