# QR Studio

A desktop app to make custom QR codes and read them from images or a camera.

## Sample

This sample QR code contains the YouTube URL `https://www.youtube.com/`. Scan it with a phone or use the app's **Scan** tab.

![Sample QR code](samples/sample_qr.png)

## Start the app

1. Install Python 3.9 or newer.
2. Open a terminal in this folder.
3. Install the required packages:

   ```bash
   py -m pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   py qr_app.py
   ```

## Workflows

![QR Studio workflows](docs/workflows.svg)

### Make a QR code

1. Open **Generate** and choose Website or text, Wi-Fi network, or Contact card.
2. Fill in the required fields marked with `*`.
3. Select **Generate and save QR code**, then choose where to save the PNG.

Website or text needs content. Wi-Fi needs a network name and password. A contact card needs a full name; phone, email, and organization are optional.

The preview refreshes shortly after you type. Choose QR and background colors, output size, and error correction before saving. Generation happens on your computer; text and URLs are not uploaded to a service. Content is limited to about 2,900 bytes so the app stays responsive and the code remains scannable.

### Read a QR code

1. Open **Scan**.
2. Choose a QR image, or open the camera scanner.
3. Read the decoded content in the Scan result box. Press **Q** to close the camera.

QR images are saved as PNG files. Camera scanning needs a working camera.
