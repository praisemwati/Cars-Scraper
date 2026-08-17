import pandas as pd

df = pd.read_csv("classifieds.co.zw_cars.csv")

df["Seller's Number"] = "+" + df["Seller's Number"].astype(str)

df.to_csv("classifieds.co.zw_cars_fixed.csv", index=False)
print("done")
