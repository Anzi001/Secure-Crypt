import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path

MY_EXTENSION = ".securecrypt"
PROG_NAME = "Secure Crypt"

class SecureVault:
    def __init__(self, root):
        self.root = root
        self.root.title(PROG_NAME)
        self.root.geometry("420x400")
        self.is_cancelled = False # Flag to track cancellation
        
        font_main = ("Segoe UI", 16, "bold") if sys.platform == "win32" else ("Helvetica", 16, "bold")
        tk.Label(root, text=PROG_NAME, font=font_main).pack(pady=15)
        tk.Label(root, text="AES-256-GCM Secure Encryption", font=("Arial", 8), fg="gray").pack()

        tk.Button(root, text="🔒 LOCK FILE", command=lambda: self.start_task(True, False), 
                  bg="#2c3e50", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=60, pady=5)
        tk.Button(root, text="🔓 UNLOCK FILE", command=lambda: self.start_task(False, False), 
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=60, pady=5)
        
        tk.Label(root, text="--- Folder Tools ---", fg="gray", font=("Arial", 7)).pack(pady=5)
        tk.Button(root, text="📂 LOCK FOLDER", command=lambda: self.start_task(True, True), 
                  bg="#34495e", fg="white", font=("Arial", 9)).pack(fill="x", padx=80, pady=2)
        tk.Button(root, text="📂 UNLOCK FOLDER", command=lambda: self.start_task(False, True), 
                  bg="#2ecc71", fg="white", font=("Arial", 9)).pack(fill="x", padx=80, pady=2)

    def get_key(self, password, salt):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
        return kdf.derive(password.encode())

    def start_task(self, encrypt, is_folder):
        path_str = filedialog.askdirectory() if is_folder else filedialog.askopenfilename()
        if not path_str: return

        pwd = simpledialog.askstring("Auth", "Enter Passcode:", show='*')
        if not pwd: return

        if encrypt:
            if pwd != simpledialog.askstring("Auth", "Confirm Passcode:", show='*'):
                messagebox.showerror("Error", "Passcodes do not match!")
                return

        self.is_cancelled = False
        popup = tk.Toplevel(self.root)
        popup.title("Processing...")
        popup.geometry("380x220")
        popup.attributes("-topmost", True)
        
        status_var = tk.StringVar(value="Analyzing...")
        tk.Label(popup, text="Current Task:", font=("Arial", 9, "bold")).pack(pady=(10, 0))
        tk.Label(popup, textvariable=status_var, font=("Arial", 9), wraplength=340).pack(pady=5)
        
        prog = ttk.Progressbar(popup, orient="horizontal", length=300, mode="determinate")
        prog.pack(pady=10)

        # Cancel Button
        def cancel():
            self.is_cancelled = True
            status_var.set("Cancelling after current file...")

        tk.Button(popup, text="Cancel Process", command=cancel, bg="#e74c3c", fg="white").pack(pady=10)

        threading.Thread(target=self.process, args=(encrypt, path_str, pwd, popup, is_folder, status_var, prog), daemon=True).start()

    def process_file(self, path, encrypt, pwd):
        path = Path(path)
        if encrypt:
            salt, nonce = os.urandom(16), os.urandom(12)
            aesgcm = AESGCM(self.get_key(pwd, salt))
            with open(path, "rb") as f: data = f.read()
            ciphertext = aesgcm.encrypt(nonce, data, None)
            new_path = path.with_suffix(path.suffix + MY_EXTENSION)
            with open(new_path, "wb") as f: f.write(salt + nonce + ciphertext)
        else:
            with open(path, "rb") as f: data = f.read()
            salt, nonce, ciphertext = data[:16], data[16:28], data[28:]
            aesgcm = AESGCM(self.get_key(pwd, salt))
            output = aesgcm.decrypt(nonce, ciphertext, None)
            new_path = path.with_name(path.name.replace(MY_EXTENSION, ""))
            with open(new_path, "wb") as f: f.write(output)
        os.remove(path)

    def process(self, encrypt, path_str, pwd, popup, is_folder, status_var, prog):
        try:
            base_path = Path(path_str)
            files = [base_path] if not is_folder else [f for f in base_path.rglob('*') if f.is_file()]
            
            # Filter valid targets
            to_do = []
            for f in files:
                if encrypt and f.suffix != MY_EXTENSION: to_do.append(f)
                elif not encrypt and f.suffix == MY_EXTENSION: to_do.append(f)

            total = len(to_do)
            for i, item in enumerate(to_do):
                if self.is_cancelled: break # Safety break
                status_var.set(f"{'Locking' if encrypt else 'Unlocking'}: {item.name}")
                prog['value'] = ((i + 1) / total) * 100
                self.process_file(item, encrypt, pwd)
            
            msg = "Operation Cancelled." if self.is_cancelled else "Operation Successful!"
            self.root.after(0, lambda: self.complete_task(popup, True, msg))
        except Exception:
            self.root.after(0, lambda: self.complete_task(popup, False))

    def complete_task(self, popup, success, msg=None):
        popup.destroy()
        if success: messagebox.showinfo("Done", msg)
        else: messagebox.showerror("Error", "Security Failure: Wrong passcode or corrupted data.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureVault(root)
    root.mainloop()
