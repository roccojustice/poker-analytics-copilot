import pandas as pd
import pytest
from analytics import analyze_metric, since_date_filter

def test_analyze_metrics():
   # Test case 1: Basic functionality
   df = pd.DataFrame({
       'pos': ['BB', 'SB', 'BB', 'SB', 'BB'], 
       'amt_won': [1, 5, -5, -4, -2] ,
       'amt_bb': [1, 0.5, 1, 2, 1],
   })
    
   result = analyze_metric(df, group_by='pos', metric='winrate')
   assert 'bb_per_100' in result.columns, "bb_per_100 column should be present in the result"
   assert 'avg_bb_per_hand' in result.columns, "avg_bb_per_hand column should be present in the result"
   assert result.loc['BB', 'hands'] == 3, "BB hands count should be 3"
   assert result.loc['SB', 'hands'] == 2, "SB hands count should be 2"
   assert result.loc['BB', 'bb_per_100'] == -200, "BB bb_per_100 should be -200"
   assert result.loc['SB', 'bb_per_100'] == 400, "SB bb_per_100 should be 400"


def test_analyze_metrics_invalid_metric():
   with pytest.raises(ValueError):
      df = pd.DataFrame({'pos': ['BB'], 'amt_won': [1], 'amt_bb': [1]})
      analyze_metric(df, group_by='pos', metric='invented_metric')

def test_since_date_filter():
   df = pd.DataFrame({
       'date_played': pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01']),
       'amt_won': [1, 2, 3]
   })

   filtered_df = since_date_filter(df, since_date='2023-02-01')
   assert list(filtered_df['amt_won']) == [2, 3], "Filtered DataFrame should have 2 rows and its 'amt_won' values should be [2, 3]"