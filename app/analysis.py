def run_analysis(stocks, targets):
    sector_quantities = {}
    for stock in stocks:
        sector = stock["sector"]
        qty = stock["quantity"]
        if sector not in sector_quantities:
            sector_quantities[sector] = 0
        sector_quantities[sector] += qty

    total_quantity = sum(sector_quantities.values())

    sector_actual_pct = {}
    for sector, qty in sector_quantities.items():
        sector_actual_pct[sector] = round((qty / total_quantity) * 100, 2)

    target_dict = {t["sector"]: t["target_pct"] for t in targets}
    all_sectors = set(list(target_dict.keys()) + list(sector_actual_pct.keys()))

    results = []
    for sector in all_sectors:
        actual_pct = sector_actual_pct.get(sector, 0.0)
        target_pct = target_dict.get(sector, 0.0)
        gap_pct = round(actual_pct - target_pct, 2)
        if abs(gap_pct) <= 5:
            status = "on-target"
        elif gap_pct > 5:
            status = "overweight"
        else:
            status = "underweight"
        results.append({
            "sector": sector,
            "actual_pct": actual_pct,
            "target_pct": target_pct,
            "gap_pct": gap_pct,
            "status": status,
        })

    results.sort(key=lambda r: abs(r["gap_pct"]), reverse=True)
    return results
