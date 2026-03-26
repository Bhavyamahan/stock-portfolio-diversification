def run_analysis(stocks, targets):
    # Calculate total VALUE per sector (quantity × buy_price)
    sector_values = {}
    for stock in stocks:
        sector = stock["sector"]
        value  = stock["quantity"] * stock.get("buy_price", 1)
        if sector not in sector_values:
            sector_values[sector] = 0
        sector_values[sector] += value

    # Grand total value of entire portfolio
    total_value = sum(sector_values.values())

    # Convert each sector's value into a percentage
    sector_actual_pct = {}
    for sector, value in sector_values.items():
        sector_actual_pct[sector] = round((value / total_value) * 100, 2)

    # Build target dict for easy lookup
    target_dict = {t["sector"]: t["target_pct"] for t in targets}
    all_sectors = set(list(target_dict.keys()) + list(sector_actual_pct.keys()))

    results = []
    for sector in all_sectors:
        actual_pct = sector_actual_pct.get(sector, 0.0)
        target_pct = target_dict.get(sector, 0.0)
        gap_pct    = round(actual_pct - target_pct, 2)
        if abs(gap_pct) <= 5:
            status = "on-target"
        elif gap_pct > 5:
            status = "overweight"
        else:
            status = "underweight"
        results.append({
            "sector":     sector,
            "actual_pct": actual_pct,
            "target_pct": target_pct,
            "gap_pct":    gap_pct,
            "status":     status,
        })

    results.sort(key=lambda r: abs(r["gap_pct"]), reverse=True)
    return results
