def run_analysis(stocks, targets):
    # Calculate total VALUE per sector (quantity x buy_price)
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
        actual_pct   = sector_actual_pct.get(sector, 0.0)
        target_pct   = target_dict.get(sector, 0.0)
        gap_pct      = round(actual_pct - target_pct, 2)
        actual_value = sector_values.get(sector, 0.0)
        target_value = round((target_pct / 100) * total_value, 2)
        gap_value    = round(actual_value - target_value, 2)

        # Status based on gap
        if abs(gap_pct) <= 5:
            status = "on-target"
        elif gap_pct > 5:
            status = "overweight"
        else:
            status = "underweight"

        # Rebalancing action
        if status == "overweight":
            action          = "Reduce"
            action_amount   = abs(gap_value)
            action_detail   = f"Move Rs.{abs(gap_value):,.0f} out of this sector"
        elif status == "underweight":
            action          = "Increase"
            action_amount   = abs(gap_value)
            action_detail   = f"Add Rs.{abs(gap_value):,.0f} into this sector"
        else:
            action          = "Hold"
            action_amount   = 0
            action_detail   = "No action needed"

        results.append({
            "sector":        sector,
            "actual_pct":    actual_pct,
            "target_pct":    target_pct,
            "gap_pct":       gap_pct,
            "actual_value":  actual_value,
            "target_value":  target_value,
            "gap_value":     gap_value,
            "status":        status,
            "action":        action,
            "action_amount": action_amount,
            "action_detail": action_detail,
        })

    # Sort by biggest gap first
    results.sort(key=lambda r: abs(r["gap_pct"]), reverse=True)

    return results, total_value
