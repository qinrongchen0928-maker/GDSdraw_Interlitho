# GDSdraw

Free web app for generating GDS files from simple periodic parameters or binary images.

## Features

- 1D grating generation using GDS array references.
- 2D circle, square, and rectangle arrays using GDS array references.
- Image-to-GDS conversion with grayscale thresholding, optional inversion, and run merging.
- Streamlit interface that can run locally or on free hosting such as Streamlit Community Cloud / Render.

## Local Run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open the local URL shown by Streamlit. A phone on the same Wi-Fi can usually open:

```text
http://YOUR_COMPUTER_IP:8501
```

On Windows, after dependencies are available, you can also run:

```powershell
.\run_local.ps1
```

## Free Deployment

### Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Create a new app in Streamlit Community Cloud.
3. Set the entry file to `app.py`.

### Render Free Web Service

1. Push this folder to a GitHub repository.
2. Create a Render Web Service from the repository.
3. Use:

```text
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Render free instances may sleep and have limited CPU/RAM, so large image-to-GDS jobs should be tested locally first.

## Notes

All geometric dimensions are in micrometers. Output files use GDS user units configured for micrometer-scale layouts.
