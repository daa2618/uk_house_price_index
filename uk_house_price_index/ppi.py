import pandas as pd

def clean_df(postcode_data:pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the postcode data DataFrame by removing rows with NaN values in the 'postcode' column.
    
    Args:
        postcode_data (pd.DataFrame): The DataFrame containing postcode data.
        
    Returns:
        pd.DataFrame: A cleaned DataFrame with rows containing NaN in 'postcode' removed.
    """
    if postcode_data.empty:
        return postcode_data
    results_df = postcode_data.sort_values("date")

    results_df["paon"] = results_df["paon"].astype(float).astype(int)
    results_df["amount"] = results_df["amount"].astype(float)
    results_df["date"] = pd.to_datetime(results_df["date"])
    results_df = results_df.assign(
        address = [f"{paon}, {street}, {postcode}" for paon, street, postcode in results_df[["paon", "street", "postcode"]].values]
    )
    return results_df

def calculate_appreciated_prices(results_df:pd.DataFrame)-> pd.DataFrame:
    if results_df.empty:
        return pd.DataFrame()
    out = []
    for address in results_df["address"].unique():
        filtered_for_address =  (
            results_df
            .loc[
            (results_df["address"]==address) & (results_df["category"]=="Standard price paid transaction")
             ]
            .reset_index(drop=True)
        )
        if filtered_for_address.empty:
            continue
        price_change = filtered_for_address["amount"].diff()
        
        n_days = filtered_for_address["date"].diff()
        if price_change.empty or n_days.empty:
            continue
        
        price_change = price_change.sum()
        n_days = n_days.sum().days#.values[-1]
        if not price_change and not n_days:
            continue
        print(f"{address=}; {price_change=}; {n_days=}")
        
        out.append(
            {
                "address" : address,
                "price_change" : price_change,
                "n_days" : n_days,
                "appreciation_per_day" : price_change / (n_days),
                "appreciation_per_year" : price_change / (n_days/365)
            }
        )
    if not out:
        return pd.DataFrame()

    return (
    pd.DataFrame(out)
    .sort_values("appreciation_per_year", 
                ascending=False)
    .reset_index(drop=True)
)
        
        
    
