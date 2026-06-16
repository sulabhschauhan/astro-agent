"""Canonical house-counting helpers including resolve_house_counting_lagna()."""


def resolve_house_counting_lagna(varshaphal_data: dict, astrosage_parsed_data: dict | None, target_year: int) -> dict:
    """
    Resolve which Lagna sign to use as the house-counting reference for
    Varshaphal-derived placements (Mudda Dasha bhav, and Muntha in a future
    follow-up): prefer AstroSage's own stated Varshaphal Lagna when it's
    available for this target_year, else fall back to this pipeline's
    computed Varshaphal Lagna.

    This exists because the computed Varshaphal Lagna can land one sign off
    from AstroSage's near a sign boundary (see
    build_varshaphal_chart's lagna_boundary_sensitive / Session 17
    ayanamsa-investigation.md) -- when AstroSage's own value is available
    for the year in question, it's a strictly better house-counting
    reference than ours.

    Args:
        varshaphal_data: dict as returned by build_varshaphal_chart(). Must
            contain "lagna" and "lagna_boundary_sensitive".
        astrosage_parsed_data: dict as returned by astrosage_parser
            .extract_varshaphal_lagna_year(), or None if no AstroSage PDF
            was supplied. Expected keys: "varshaphal_lagna" (str | None),
            "varsha_year" (int | None).
        target_year: Gregorian year of the Varshaphal.

    Returns:
        {
          "lagna_sign": str,
          "source": "astrosage" | "computed",
          "boundary_sensitive": bool,  # always False when source=="astrosage"
        }

    Raises:
        ValueError: varshaphal_data is missing "lagna" or
            "lagna_boundary_sensitive".
    """
    try:
        computed_lagna = varshaphal_data["lagna"]
        boundary_sensitive = varshaphal_data["lagna_boundary_sensitive"]
    except KeyError as exc:
        raise ValueError(
            f"resolve_house_counting_lagna: varshaphal_data missing required field {exc}"
        ) from exc

    if astrosage_parsed_data:
        astrosage_lagna = astrosage_parsed_data.get("varshaphal_lagna")
        astrosage_year = astrosage_parsed_data.get("varsha_year")
        if astrosage_lagna and astrosage_year == target_year:
            return {
                "lagna_sign": astrosage_lagna,
                "source": "astrosage",
                "boundary_sensitive": False,
            }

    return {
        "lagna_sign": computed_lagna,
        "source": "computed",
        "boundary_sensitive": boundary_sensitive,
    }
