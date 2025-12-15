import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor as Pool

def make_csv_files(size):
    for i in range(1, 6):
        df = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C', 'D'], size),
            'value': np.random.uniform(0, 1000, size)
        })
        df.to_csv('csvFiles/data' + str(i) + '.csv')

def process_csv_file(file_name):
    df = pd.read_csv(file_name)
    result = df.groupby('category')['value'].aggregate(['median','std']).reset_index()
    return result

if __name__ == "__main__":
    make_csv_files(100)

    filename_array = ['csvFiles/Data1.csv', 'csvFiles/Data2.csv', 'csvFiles/Data3.csv', 'csvFiles/Data4.csv', 'csvFiles/Data5.csv']
    results = list(Pool().map(process_csv_file, filename_array))
    for i in range(0, len(results)):
        print('Data from file csvFiles/data', i + 1, '.csv:', sep='')
        print(results[i], end='\n\n')

    print('Recycled results:')

    print(pd.concat(results).groupby('category')['median'].aggregate([('median median', 'median'),('median std', 'std')]).reset_index())
