from datetime import datetime, timezone
import pandas as pd
import matplotlib.pyplot as plt


# Load dat_kp.parquet Parquet file
path = 'enter you own path to parsed data folder'
df = pd.read_parquet(path)

##### Keyboard Usage Graph #####
# make copy of dataframe
df_copy = df.copy()
# convert to Chicago time (switch to whichever timezone you're in) 
df_copy["keypress_timestamp_chicago"] = pd.to_datetime(df_copy["keypress_timestamp"], utc=True).dt.tz_convert("America/Chicago")

# get dates only
df_copy['Dates'] = pd.to_datetime(df_copy['keypress_timestamp_chicago'].dt.date)
# get hour only
df_copy['Hours'] = df_copy['keypress_timestamp_chicago'].dt.hour

# convert hours into float
df_copy["hour_float"] = df_copy["Hours"] + df_copy["keypress_timestamp_chicago"].dt.minute/ 60
# get total count for each keypress at each hour
df_totals = df_copy.groupby(["hour_float", "Dates"]).size().reset_index(name="count")

# sort dates into chronological order
df_totals = df_totals.sort_values(by="Dates")
# format date  ex) July 15
df_totals["Dates"] = df_totals["Dates"].dt.strftime('%B %d')

x = df_totals["hour_float"]
y = df_totals["Dates"]
# plot the graph
plt.figure(figsize=(6,6))
scatter = plt.scatter(x,y, s=df_totals["count"], color = "blue")
plt.xticks([0, 6, 12, 18], ['Midnight', '6 AM', 'Noon', '6 PM'])
plt.title(f"Keyboard Usage", fontname="Helvetica", fontsize = 18)
plt.xlabel("Time", fontname = "Helvetica", fontsize = 12)   
plt.ylabel("Date", fontname = "Helvetica", fontsize = 12)
handles, labels = scatter.legend_elements("sizes", num=3,color = "blue")
labels = [f"{label} keys" for label in labels]
plt.legend(handles, labels)
plt.tight_layout()
plt.grid()
plt.show()

##### Keyboard Orientation Usage Graph #####
# Load dat_ses.parquet Parquet file
path = 'enter you own path to parsed data folder'
ses = pd.read_parquet(path)
# merge dat_ses.parquet and dat_kp.parquet dataframes
tk = pd.merge(ses, df_copy)

# create count column for number of keypresses
tk_copy = tk.groupby(["hour_float", "Dates","upright"]).size().reset_index(name="count")
# sort dates into chronological order
tk_copy = tk_copy.sort_values(by="Dates")
# format date ex) July 15
tk_copy["Dates"] = tk_copy["Dates"].dt.strftime('%B %d')

# get the hours and dates of keyboard sessions that are upright 
x1 = tk_copy["hour_float"].loc[tk_copy["upright"] == True] 
y1 = tk_copy["Dates"].loc[tk_copy["upright"] == True] 
# get the hours and dates of keyboard sessions that are reclined 
x2 = tk_copy["hour_float"].loc[tk_copy["upright"] == False]
y2 = tk_copy["Dates"].loc[tk_copy["upright"] == False] 

# plot the graph
plt.figure(figsize=(6,6))
plt.scatter(x1, y1, c="#ADD8E6",s= tk_copy["count"].loc[tk_copy["upright"] == True] , label='Upright')
plt.scatter(x2, y2, c='blue',s=tk_copy["count"].loc[tk_copy["upright"] == False] , label='Reclined')
plt.xticks([0, 6, 12, 18], ['Midnight', '6 AM', 'Noon', '6 PM'])
plt.xlabel("Time", fontname = "Helvetica", fontsize = 12)   
plt.ylabel("Date", fontname = "Helvetica", fontsize = 12)
plt.title(f"Keyboard Orientation Usage", fontname="Helvetica", fontsize = 18)
plt.legend()
plt.tight_layout()
plt.grid()
plt.show()

##### Daily Keypress Count Graph #####  

# print(tk["totalKeyPresses"].sum())

# computes sum of total keypresses that occurred each day
tk_copy = tk.groupby("Dates")["totalKeyPresses"].sum().reset_index(name="count_per_day")
# sort dates into chronological order
tk_copy = tk_copy.sort_values(by="Dates")
# format date ex) July 15
tk_copy["Dates"] = tk_copy["Dates"].dt.strftime('%B %d')
x = tk_copy['Dates']
y = tk_copy["count_per_day"]

# plot the graph
plt.figure(figsize=(6,6))
plt.scatter(x,y, color="blue", label="Keypresses")
plt.plot(x,y,linestyle="solid", marker=".",markersize = 15, markerfacecolor="white", color="blue")
plt.xlabel("Date", fontname = "Helvetica", fontsize = 12)   
plt.ylabel("Keypresses", fontname = "Helvetica", fontsize = 12)
plt.title(f"Daily Keypress Count", fontname="Helvetica", fontsize = 18)
plt.legend()
plt.tight_layout()
plt.grid()
plt.xticks(rotation='vertical')
plt.show()


