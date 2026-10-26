"""Download the UCI Online Retail dataset (about 45 MB) into data/.

  python download_data.py
"""
import pathlib, urllib.request

URL = ("https://raw.githubusercontent.com/databricks/Spark-The-Definitive-Guide/"
       "master/data/retail-data/all/online-retail-dataset.csv")
dest = pathlib.Path("data/online-retail-dataset.csv")
dest.parent.mkdir(exist_ok=True)
print("Downloading...")
urllib.request.urlretrieve(URL, dest)
print("Saved", dest, f"({dest.stat().st_size/1e6:.1f} MB)")
