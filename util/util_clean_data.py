import pandas as pd

def left_join_df_on_ind(left_df: pd.DataFrame, right_df:
                        pd.DataFrame) -> pd.DataFrame:
    return pd.merge(left_df, right_df, how='left', left_index=True,
                    right_index=True)