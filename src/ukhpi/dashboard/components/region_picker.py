from __future__ import annotations

import pandas as pd

_REGION_TYPE_ORDER = ["Country", "Region", "UnitaryAuthority", "AdminDistrict", "LondonBorough"]


def build_region_options(regions_df: pd.DataFrame) -> list[dict]:
    """Return Dropdown options grouped by region type with type-prefixed labels.

    Mantine + dcc.Dropdown have no native optgroup, so the prefix gives users a visible
    hierarchy hint while keeping `value` as a flat slug.
    """
    if "ref_region_type_keyword" not in regions_df.columns:
        return [{"label": f"🏠 {r.title()}", "value": r} for r in regions_df["ref_region_keyword"].unique()]

    options: list[dict] = []
    seen: set[str] = set()
    type_to_emoji = {
        "Country": "🌍",
        "Region": "🗺️",
        "UnitaryAuthority": "🏛️",
        "AdminDistrict": "📍",
        "LondonBorough": "🏙️",
    }
    ordered_types = _REGION_TYPE_ORDER + sorted(
        set(regions_df["ref_region_type_keyword"].dropna().unique()) - set(_REGION_TYPE_ORDER)
    )

    for region_type in ordered_types:
        rows = regions_df[regions_df["ref_region_type_keyword"] == region_type]
        emoji = type_to_emoji.get(region_type, "🏠")
        for slug in sorted(rows["ref_region_keyword"].dropna().unique()):
            if slug in seen:
                continue
            seen.add(slug)
            options.append({"label": f"{emoji} {slug.replace('-', ' ').title()}", "value": slug})

    return options
