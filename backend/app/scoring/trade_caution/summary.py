from __future__ import annotations


def compose_trade_caution_summary(
    *,
    level: str,
    admin_caution: int,
    execution_caution: int,
    concentration_caution: int,
    behavioural_caution: int,
    rug_probability: int,
) -> str:
    if rug_probability >= 60 and level in {"high", "avoid"}:
        return (
            "Trading conditions are highly unfavorable due to scam-linked behaviour, weak liquidity structure, "
            "and concentrated control signals."
        )
    if rug_probability <= 25 and level in {"high", "avoid"}:
        return (
            "Low rug probability, but trading conditions remain unfavorable due to administrative permissions, "
            "market depth constraints, or concentration risk."
        )
    if behavioural_caution >= 60:
        return "Trading conditions are unfavorable because behaviour-linked exit or coordination risks were detected."
    if execution_caution >= 65 and admin_caution >= 50:
        return "Trading conditions are unfavorable due to administrative permissions and weak pool depth."
    if execution_caution >= 65:
        return "Trading conditions are unfavorable because liquidity depth and exit reliability are currently weak."
    if concentration_caution >= 60:
        return "Trading conditions warrant caution because holder concentration could amplify price impact."
    if admin_caution >= 55:
        return "Trading conditions warrant caution because active administrative permissions increase operational risk."
    return "Trading conditions appear relatively stable, though standard execution and contract risks still apply."
