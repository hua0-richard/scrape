import pandas as pd

for ind in [53,54,55,56]:
     aisle = "Dairy, Eggs & Fridge"
     paths = []
     for j in range(0, 12):
        paths.append('output/tmp/ind' + str(ind) + 'aisle-sub_' + str(aisle) + ' ' + str(j) + '.csv')
    
     combined_csv = pd.concat(pd.read_csv(f) for f in paths).drop_duplicates()
     combined_csv.to_csv(f"{ind}Coles_Dairy_Complete_2.csv", index=False)
