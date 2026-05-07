import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path

# --- CONFIGURATION ---
MY_EXTENSION = ".securecrypt"
PROG_NAME = "Secure Crypt"

def setup_windows_registry():
    """One-time registry association for Windows users."""
    if sys.platform == "win32":
        import ctypes
        import winreg
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                script = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
                ctypes.windll.shell32.ShellExecuteW(None, "runas", script, " ".join(sys.argv[1:]), None, 1)
                sys.exit()
            
            exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
            app_command = f'"{exe_path}" "%1"'
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, MY_EXTENSION) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "LockedFile")
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"LockedFile\shell\open\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, app_command)
        except: pass

class SecureVault:
    def __init__(self, root):
        self.root = root
        self.root.title(PROG_NAME)
        self.root.geometry("420x350")
        
        # Use cross-platform system font fallbacks
        font_main = ("Segoe UI", 16, "bold") if sys.platform == "win32" else ("Helvetica", 16, "bold")
        
        tk.Label(root, text=PROG_NAME, font=font_main).pack(pady=15)
        tk.Label(root, text="AES-256-GCM Quantum-Resistant", font=("Arial", 8), fg="gray").pack()
        
        # Action Buttons
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
        if is_folder:
            path_str = filedialog.askdirectory(title="Select Folder")
        else:
            ftypes = [("Locked Files", f"*{MY_EXTENSION}"), ("All Files", "*.*")] if not encrypt else [("All Files", "*.*")]
            path_str = filedialog.askopenfilename(filetypes=ftypes)

        if not path_str: return
        pwd = simpledialog.askstring("Auth", "Enter Passcode:", show='*')
        if not pwd: return

        # Windows-style Progress Popup
        popup = tk.Toplevel(self.root)
        popup.title("Processing...")
        popup.geometry("350x150")
        popup.attributes("-topmost", True)
        
        tk.Label(popup, text=f"{'Locking' if encrypt else 'Unlocking'} item(s)...", font=("Arial", 10)).pack(pady=10)
        prog = ttk.Progressbar(popup, orient="horizontal", length=280, mode="indeterminate")
        prog.pack(pady=10)
        prog.start(10)

        threading.Thread(target=self.process, args=(encrypt, path_str, pwd, popup, is_folder), daemon=True).start()

    def process_file(self, path, aesgcm_factory, encrypt, pwd):
        """Internal helper to handle single file crypto."""
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
            new_path = Path(str(path)[:-len(MY_EXTENSION)]) if str(path).endswith(MY_EXTENSION) else path.with_suffix('')
            with open(new_path, "wb") as f: f.write(output)
        os.remove(path)

    def process(self, encrypt, path_str, pwd, popup, is_folder):
        try:
            base_path = Path(path_str)
            if is_folder:
                # Iterate all files in directory using pathlib
                for item in base_path.iterdir():
                    if item.is_file():
                        if not encrypt and not str(item).endswith(MY_EXTENSION): continue
                        if encrypt and str(item).endswith(MY_EXTENSION): continue
                        self.process_file(item, AESGCM, encrypt, pwd)
            else:
                self.process_file(base_path, AESGCM, encrypt, pwd)
            
            self.root.after(0, popup.destroy)
            messagebox.showinfo("Done", "Operation Successful!")
        except Exception:
            self.root.after(0, popup.destroy)
            messagebox.showerror("Error", "Security Failure: Wrong passcode or corrupted data.")

if __name__ == "__main__":
    if sys.platform == "win32" and len(sys.argv) == 1:
        setup_windows_registry()
    root = tk.Tk()
    app = SecureVault(root)
    root.mainloop()
