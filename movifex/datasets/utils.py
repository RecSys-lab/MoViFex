import pandas as pd

def printTextualDatasetStats(data: pd.DataFrame):
    """
    Print dataset statistics including total interactions, unique users, items, and interaction ratios.
    Hint: The input DataFrame should have 'userId' and 'itemId' columns.

    Parameters
    ----------
    data: pd.DataFrame
        Given dataset in the form of a DataFrame.
    """
    # Variables
    totalInteractions = data.shape[0]
    uniqueUsers = data['userId'].nunique()
    uniqueItems = data['itemId'].nunique()
    # Print
    print("--------------------------")
    print("- The Dataset Overview:")
    print(f"-- Total Interactions: {totalInteractions}")
    print(f"-- |U|: {uniqueUsers}")
    print(f"-- |I|: {uniqueItems}")
    print(f"-- |R|/|U|: {totalInteractions / uniqueUsers:.2f}")
    print(f"-- |R|/|I|: {totalInteractions / uniqueItems:.2f}")
    print(f"-- |R|/(|U|*|I|): {totalInteractions / (uniqueUsers * uniqueItems):.10f}")
    print("--------------------------")

def applyInteractionLimits(data: pd.DataFrame, minInteraction: int, maxInteraction: int,
                           userColumnName: str='userId'):
    """
    Filter users based on interaction limits.

    Parameters
    ----------
    data: pd.DataFrame
        DataFrame with interactions.
    minInteraction: int
        Minimum number of interactions per user.
    maxInteraction: int
        Maximum number of interactions per user.
    userColumnName: str
        Column name for users.
    
    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    # Variables
    interactionCount = data[userColumnName].value_counts()
    # Filter which users to keep
    usersToKeep = interactionCount[(interactionCount >= minInteraction) & (interactionCount <= maxInteraction)].index
    # Return the filtered DataFrame
    return data[data[userColumnName].isin(usersToKeep)]