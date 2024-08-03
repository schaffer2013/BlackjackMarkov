import pandas as pd

def remove_rows_closest_to_times(file_path, target_times):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    removed_rows = []
    
    for target_time in target_times:
        # Find the row whose 'time(s)' column is closest to the target_time
        closest_row_index = (df['time(s)'] - target_time).abs().idxmin()
        
        # Get the row data for reference
        closest_row = df.loc[closest_row_index]
        removed_row_tuple = (closest_row['Player Low Card'], closest_row['Player High Card'], closest_row['Dealer Upcard'])
        removed_rows.append(removed_row_tuple)
        
        # Remove the row from the DataFrame
        df = df.drop(closest_row_index).reset_index(drop=True)
    
    return removed_rows

def geometric_series(sum_of_series, num_elements, first_element):
    # Calculate the common ratio using the sum formula for geometric series
    # S_n = a * (1 - r^n) / (1 - r)
    a = first_element
    S_n = sum_of_series
    n = num_elements

    if n == 1:
        return [a]

    # Using a binary search to find the common ratio r
    def find_r(a, S_n, n):
        low, high = 0, 100  # Initial range for r
        epsilon = 1e-9  # Precision of the result

        while high - low > epsilon:
            mid = (low + high) / 2
            sum_mid = a * (1 - mid**n) / (1 - mid)
            
            if sum_mid < S_n:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2

    r = find_r(a, S_n, n)

    # Generate the series
    series = [a * r**i for i in range(n)]
    return series

def get():
    # Example usage:
    sum_of_series = 7200
    num_elements = 100
    first_element = 1.0

    # Example usage:
    file_path = 'blackjack_ev_results_1_decks-baseline.csv'
    target_times = geometric_series(sum_of_series, num_elements, first_element)
    #print(target_times)

    removed_rows = remove_rows_closest_to_times(file_path, target_times)
    #print("Removed Rows (as tuples):")
    #print(removed_rows)
    return removed_rows