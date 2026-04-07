def get_power_column(df):
    """
    Returns the correct power column name present in the dataframe.

    Priority:
        1. accumulated_power
        2. total_work

    Raises:
        ValueError: If neither column exists.
    """
    if "accumulated_power" in df.columns:
        return "accumulated_power"
    if "total_work" in df.columns:
        return "total_work"

    raise ValueError("No power column found (expected 'accumulated_power' or 'total_work')")