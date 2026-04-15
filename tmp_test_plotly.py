import plotly.express as px
import io
fig = px.bar(x=[1, 2, 3], y=[4, 5, 6])
try:
    img_bytes = fig.to_image(format="png")
    print("Success: to_image works.")
except Exception as e:
    print(f"Error: {e}")
