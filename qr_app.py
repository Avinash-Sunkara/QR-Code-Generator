import qrcode
import os
import cv2

# ----------- QR GENERATOR -----------
data = input("Enter the text or URL to encode in QR: ")

qr = qrcode.make(data)

folder = "qrcodes"
os.makedirs(folder, exist_ok=True)

filename = os.path.join(folder, "qr_code.png")
qr.save(filename)

print(f"QR Code saved at {filename}")


# ----------- QR SCANNER -----------
path = input("Enter path to QR image (or press Enter to open webcam): ")

detector = cv2.QRCodeDetector()

# Scan from image
if path:
    img = cv2.imread(path)

    data, bbox, _ = detector.detectAndDecode(img)

    if data:
        print("QR Code Data:", data)
    else:
        print("No QR Code found.")

# Scan from webcam
else:
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            print("QR Code Detected:", data)
            break

        cv2.imshow("QR Scanner - Press 'q' to Quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()