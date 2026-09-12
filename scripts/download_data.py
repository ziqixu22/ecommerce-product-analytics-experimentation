from pathlib import Path
import io
import zipfile
import requests

UCI_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
CRITEO_URL = "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz"


def download(url: str) -> bytes:
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    return r.content


def main():
    raw = Path("data/raw")
    retail = raw / "online_retail_ii"
    criteo = raw / "criteo"
    retail.mkdir(parents=True, exist_ok=True)
    criteo.mkdir(parents=True, exist_ok=True)

    uci_bytes = download(UCI_URL)
    with zipfile.ZipFile(io.BytesIO(uci_bytes)) as z:
        z.extractall(retail)
    print(f"UCI Online Retail II extracted to {retail}")

    out = criteo / "criteo-research-uplift-v2.1.csv.gz"
    out.write_bytes(download(CRITEO_URL))
    print(f"Criteo Uplift downloaded to {out}")


if __name__ == "__main__":
    main()
