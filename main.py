import os, sys, base64, subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from pathlib import Path

MY_EXTENSION = ".locked"
PROG_NAME = "File Encrypter"

def setup_windows_registry():
    """Request Admin and register .locked file association on Windows."""
    if sys.platform == "win32":
        import ctypes
        import winreg
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                # Re-run with admin privileges
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
            
            # Register extension
            app_path = f'"{sys.executable}" "%1"'
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, MY_EXTENSION) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "LockedFile")
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"LockedFile\shell\open\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, app_path)
        except:
            pass # Fails gracefully if user denies admin

class SecureVault:
    def __init__(self, root):
        self.root = root
        self.root.title(PROG_NAME)
        self.root.geometry("400x250")
        
        self.main_label = tk.Label(root, text=PROG_NAME, font=("Arial", 14, "bold"))
        self.main_label.pack(pady=20)

        self.lock_btn = tk.Button(root, text="🔒 Lock File", command=lambda: self.process(True), bg="#4a90e2", fg="black")
        self.lock_btn.pack(fill="x", padx=50, pady=5)

        self.unlock_btn = tk.Button(root, text="🔓 Unlock File", command=lambda: self.process(False), bg="#5cb85c", fg="black")
        self.unlock_btn.pack(fill="x", padx=50, pady=5)

        # Handle file passed via double-click
        if len(sys.argv) > 1 and sys.argv[1].endswith(MY_EXTENSION):
            self.root.after(500, lambda: self.process(encrypt=False, file_path=sys.argv[1]))

    def get_key(self, password, salt):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def process(self, encrypt=True, file_path=None):
        path_str = file_path if file_path else filedialog.askopenfilename()
        if not path_str: return
        path = Path(path_str)
        pwd = simpledialog.askstring("Security", "Enter Passcode:", show='*')
        if not pwd: return

        try:
            if encrypt:
                salt = os.urandom(16)
                fernet = Fernet(self.get_key(pwd, salt))
                with open(path, "rb") as f: data = f.read()
                output = salt + fernet.encrypt(data)
                new_path = path.with_suffix(path.suffix + MY_EXTENSION)
            else:
                with open(path, "rb") as f: data = f.read()
                salt, actual_data = data[:16], data[16:]
                fernet = Fernet(self.get_key(pwd, salt))
                output = fernet.decrypt(actual_data)
                new_path = path.with_suffix('')

            with open(new_path, "wb") as f: f.write(output)
            os.remove(path)
            messagebox.showinfo("Success", "Operation Complete!")
        except:
            messagebox.showerror("Error", "Invalid passcode or file.")

if __name__ == "__main__":
    if sys.platform == "win32" and len(sys.argv) == 1:
        setup_windows_registry()
    root = tk.Tk()
    app = SecureVault(root)
    root.mainloop()
