import pandas as pd

df = pd.read_excel(r'..\task1_data_collection\data\data_cleaned.xlsx')
print("Columns:", df.columns.tolist())
for idx, row in df.iterrows():
    print(f"\n--- {row['景区名称']} 官方路线 ---")
    print(row['官方游览路线'])
