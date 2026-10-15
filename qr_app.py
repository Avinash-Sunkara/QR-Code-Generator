"""A small desktop QR code generator and scanner."""

from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from PIL import ImageTk

try:
    import qrcode
    import cv2
except ImportError as exc:
    raise SystemExit("Install the packages in requirements.txt, then run this app again.") from exc


BG = "#f3f6fb"
INK = "#17243a"
BLUE = "#2457d6"


class QRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QR Studio")
        self.geometry("760x640")
        self.minsize(680, 580)
        self.configure(bg=BG)
        self.output_dir = Path.cwd() / "qrcodes"
        self.output_dir.mkdir(exist_ok=True)
        self.fields = {}
        self.kind = tk.StringVar(value="Website or text")
        self.status = tk.StringVar(value="Ready when you are.")
        self.preview_job = None
        self.preview_photo = None
        self.foreground = tk.StringVar(value="#17243a")
        self.background = tk.StringVar(value="#ffffff")
        self.box_size = tk.IntVar(value=10)
        self.error_level = tk.StringVar(value="M (balanced)")
        self._style()
        self._build()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background=BG, foreground=INK, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground=INK)
        style.configure("Hint.TLabel", foreground="#63718a", font=("Segoe UI", 9))
        style.configure("Card.TLabel", background="white", foreground=INK, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="white", foreground=INK, font=("Segoe UI", 14, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(14, 9))
        style.configure("Accent.TButton", background=BLUE, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#1946b7")])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(20, 10), font=("Segoe UI", 10, "bold"))

    def _build(self):
        outer = ttk.Frame(self, padding=28)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="QR Studio", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Create a QR code or scan one in a few simple steps.", style="Hint.TLabel").pack(anchor="w", pady=(3, 20))
        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)
        self.generate_tab = ttk.Frame(self.tabs, padding=22)
        self.scan_tab = ttk.Frame(self.tabs, padding=22)
        self.tabs.add(self.generate_tab, text="  Generate  ")
        self.tabs.add(self.scan_tab, text="  Scan  ")
        self._build_generate()
        self._build_scan()
        ttk.Label(outer, textvariable=self.status, style="Hint.TLabel").pack(anchor="w", pady=(14, 0))

    def _build_generate(self):
        card = ttk.Frame(self.generate_tab, style="Card.TFrame", padding=22)
        card.pack(fill="both", expand=True)
        ttk.Label(card, text="Build your QR code", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text="Choose a format, fill in the required details, then save your image.", style="Hint.TLabel").pack(anchor="w", pady=(4, 18))
        ttk.Label(card, text="QR code type", style="Card.TLabel").pack(anchor="w")
        choices = ttk.Combobox(card, textvariable=self.kind, values=["Website or text", "Wi-Fi network", "Contact card"], state="readonly")
        choices.pack(fill="x", pady=(6, 16))
        choices.bind("<<ComboboxSelected>>", lambda _event: self._render_fields())
        self.form = ttk.Frame(card, style="Card.TFrame")
        self.form.pack(fill="x", expand=True)
        self._render_fields()
        options = ttk.Frame(card, style="Card.TFrame")
        options.pack(fill="x", pady=(10, 2))
        ttk.Label(options, text="Style", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Button(options, text="QR color", command=lambda: self._choose_color(self.foreground)).grid(row=0, column=1, padx=3)
        ttk.Button(options, text="Background", command=lambda: self._choose_color(self.background)).grid(row=0, column=2, padx=3)
        ttk.Label(options, text="Size", style="Card.TLabel").grid(row=0, column=3, padx=(12, 4))
        size_choice = ttk.Combobox(options, textvariable=self.box_size, values=(6, 8, 10, 12, 14), state="readonly", width=4)
        size_choice.grid(row=0, column=4)
        size_choice.bind("<<ComboboxSelected>>", self._schedule_preview)
        ttk.Label(options, text="Error correction", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        correction = ttk.Combobox(options, textvariable=self.error_level, values=("L (small)", "M (balanced)", "Q (high)", "H (highest)"), state="readonly", width=18)
        correction.grid(row=1, column=1, columnspan=2, sticky="w", pady=(10, 0))
        correction.bind("<<ComboboxSelected>>", self._schedule_preview)
        options.columnconfigure(5, weight=1)
        ttk.Label(card, text="Live preview updates as you type.", style="Hint.TLabel").pack(anchor="w", pady=(14, 0))
        self.preview = ttk.Label(card, text="Enter content to preview", style="Hint.TLabel", anchor="center")
        self.preview.pack(anchor="center", pady=(3, 0))
        ttk.Button(card, text="Generate and save QR code", style="Accent.TButton", command=self.generate).pack(anchor="w", pady=(18, 0))

    def _render_fields(self):
        for child in self.form.winfo_children():
            child.destroy()
        self.fields.clear()
        if self.kind.get() == "Website or text":
            specs = [("content", "Text or URL *", "https://example.com")]
        elif self.kind.get() == "Wi-Fi network":
            specs = [("ssid", "Network name (SSID) *", ""), ("password", "Password *", ""), ("security", "Security", "WPA")]
        else:
            specs = [("name", "Full name *", ""), ("phone", "Phone", ""), ("email", "Email", ""), ("organization", "Organization", "")]
        for key, label, hint in specs:
            ttk.Label(self.form, text=label, style="Card.TLabel").pack(anchor="w", pady=(4, 5))
            entry = ttk.Entry(self.form, font=("Segoe UI", 10))
            entry.pack(fill="x", ipady=7, pady=(0, 7))
            if hint:
                entry.insert(0, hint)
                if key == "content":
                    entry.bind("<FocusIn>", lambda _e, w=entry: w.delete(0, "end") if w.get() == "https://example.com" else None)
            self.fields[key] = entry
            entry.bind("<KeyRelease>", self._schedule_preview)
        self._schedule_preview()

    def _schedule_preview(self, _event=None):
        if self.preview_job is not None:
            self.after_cancel(self.preview_job)
        self.preview_job = self.after(250, self._render_preview)

    def _render_preview(self):
        self.preview_job = None
        payload = self._get_payload(show_error=False)
        if not payload:
            self.preview.configure(image="", text="Enter required details to preview")
            self.preview_photo = None
            return
        try:
            image = self._make_qr(payload).make_image(fill_color=self.foreground.get(), back_color=self.background.get())
            image = image.convert("RGB")
            image.thumbnail((164, 164))
            self.preview_photo = ImageTk.PhotoImage(image)
            self.preview.configure(image=self.preview_photo, text="")
        except (ValueError, TypeError):
            self.preview.configure(image="", text="Choose valid QR and background colors")
            self.preview_photo = None

    def _choose_color(self, variable):
        color = colorchooser.askcolor(color=variable.get(), parent=self, title="Choose a QR color")
        if color and color[1]:
            variable.set(color[1])
            self._schedule_preview()

    def _get_payload(self, show_error=True):
        values = {key: entry.get().strip() for key, entry in self.fields.items()}
        kind = self.kind.get()
        if kind == "Website or text":
            payload = values["content"]
            if not payload or payload == "https://example.com":
                if show_error:
                    self._invalid("Enter the text or URL you want to encode.")
                return None
        elif kind == "Wi-Fi network":
            if not values["ssid"] or not values["password"]:
                if show_error:
                    self._invalid("Network name and password are required for a Wi-Fi QR code.")
                return None
            payload = f"WIFI:T:{values['security'] or 'WPA'};S:{self._escape(values['ssid'])};P:{self._escape(values['password'])};;"
        else:
            if not values["name"]:
                if show_error:
                    self._invalid("A full name is required for a contact card.")
                return None
            payload = "BEGIN:VCARD\nVERSION:3.0\n" + f"FN:{values['name']}\n"
            for key, prop in (("phone", "TEL"), ("email", "EMAIL"), ("organization", "ORG")):
                if values[key]:
                    payload += f"{prop}:{values[key]}\n"
            payload += "END:VCARD"
        if len(payload.encode("utf-8")) > 2900:
            if show_error:
                self._invalid("This QR code is too large. Keep the content under about 2,900 bytes.")
            return None
        return payload

    def _make_qr(self, payload):
        levels = {"L (small)": qrcode.constants.ERROR_CORRECT_L,
                  "M (balanced)": qrcode.constants.ERROR_CORRECT_M,
                  "Q (high)": qrcode.constants.ERROR_CORRECT_Q,
                  "H (highest)": qrcode.constants.ERROR_CORRECT_H}
        qr = qrcode.QRCode(version=None, error_correction=levels[self.error_level.get()], box_size=self.box_size.get(), border=4)
        qr.add_data(payload)
        qr.make(fit=True)
        return qr

    def generate(self):
        payload = self._get_payload()
        if not payload:
            return
        path = filedialog.asksaveasfilename(title="Save QR code", initialdir=str(self.output_dir), initialfile="qr_code.png", defaultextension=".png", filetypes=[("PNG image", "*.png")])
        if not path:
            self.status.set("Save cancelled. Your details are still here.")
            return
        try:
            self._make_qr(payload).make_image(fill_color=self.foreground.get(), back_color=self.background.get()).save(path)
            self.status.set(f"QR code saved: {path}")
            messagebox.showinfo("QR code ready", f"Your QR code was saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Could not create QR code", str(exc))

    @staticmethod
    def _escape(value):
        return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")

    def _build_scan(self):
        card = ttk.Frame(self.scan_tab, style="Card.TFrame", padding=22)
        card.pack(fill="both", expand=True)
        ttk.Label(card, text="Read a QR code", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text="Choose an image file or use your computer's camera.", style="Hint.TLabel").pack(anchor="w", pady=(4, 20))
        ttk.Button(card, text="Choose QR image…", style="Accent.TButton", command=self.scan_image).pack(anchor="w")
        ttk.Label(card, text="or", style="Hint.TLabel").pack(anchor="w", pady=12)
        ttk.Button(card, text="Open camera scanner", command=self.scan_camera).pack(anchor="w")
        ttk.Label(card, text="Camera scan: point the code at the camera. Press Q to close.", style="Hint.TLabel").pack(anchor="w", pady=(10, 22))
        ttk.Label(card, text="Scan result", style="Card.TLabel").pack(anchor="w", pady=(0, 6))
        self.result = tk.Text(card, height=7, wrap="word", font=("Consolas", 10), relief="solid", bd=1, padx=10, pady=9)
        self.result.pack(fill="both", expand=True)
        self.result.configure(state="disabled")

    def _show_result(self, text):
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", text)
        self.result.configure(state="disabled")
        self.status.set("QR code scanned successfully." if text else "No QR code was found in that image.")

    def scan_image(self):
        path = filedialog.askopenfilename(title="Choose a QR image", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")])
        if not path:
            return
        image = cv2.imread(path)
        if image is None:
            return self._invalid("That image could not be opened. Choose a valid image file.")
        data, _points, _straight = cv2.QRCodeDetector().detectAndDecode(image)
        self._show_result(data or "No QR code found. Try a clearer image with the full code visible.")

    def scan_camera(self):
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            camera.release()
            return self._invalid("Could not open the camera. Check that it is connected and available.")
        detector = cv2.QRCodeDetector()
        found = ""
        try:
            while True:
                ok, frame = camera.read()
                if not ok:
                    break
                data, points, _straight = detector.detectAndDecode(frame)
                if points is not None:
                    points = points.astype(int).reshape(-1, 2)
                    for index in range(len(points)):
                        cv2.line(frame, tuple(points[index]), tuple(points[(index + 1) % len(points)]), (50, 210, 100), 3)
                cv2.imshow("QR Studio — press Q to close", frame)
                if data:
                    found = data
                    break
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            camera.release()
            cv2.destroyAllWindows()
        if found:
            self._show_result(found)
        else:
            self.status.set("Camera scanner closed.")

    def _invalid(self, message):
        self.status.set(message)
        messagebox.showwarning("Check required information", message)


if __name__ == "__main__":
    QRApp().mainloop()
