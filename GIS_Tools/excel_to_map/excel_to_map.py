import pandas as pd
import folium
import os

BASE_DIR=os.path.dirname(__file__)

data_path=os.path.join(BASE_DIR,"data","data.xlsx")
output_path=os.path.join(BASE_DIR,"output","map.html")

df=pd.read_excel(data_path)

center=[df.loc[0,"lat"],df.loc[0,"lon"]]
m=folium.Map(location=center,zoom_start=12)

for _, row in df.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=str(row["name"])
    ).add_to(m)

m.save(output_path)

print(f"Map generated successfully and saved to {output_path}")