import os, sys, base64
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path

# --- CONFIGURATION ---
MY_EXTENSION = ".locked"
PROG_NAME = "Quantum-Vault"

def setup_windows_registry():
    """Register .locked file association for Windows."""
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
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"LockedFile\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{exe_path},0")
        except:
            pass

class SecureVault:
    def __init__(self, root):
        self.root = root
        self.root.title(PROG_NAME)
        self.root.geometry("400x280")
        
        tk.Label(root, text=PROG_NAME, font=("Arial", 16, "bold")).pack(pady=15)
        tk.Label(root, text="AES-256-GCM Quantum-Resistant", font=("Arial", 8), fg="gray").pack()

        tk.Button(root, text="🔒 LOCK FILE", command=lambda: self.process(True), 
                  bg="#2c3e50", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=50, pady=10)

        tk.Button(root, text="🔓 UNLOCK FILE", command=lambda: self.process(False), 
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=50, pady=5)

        # File association trigger
        if len(sys.argv) > 1 and sys.argv[1].endswith(MY_EXTENSION):
            self.root.after(500, lambda: self.process(encrypt=False, file_path=sys.argv[1]))

    def get_key(self, password, salt):
        """Derives a 256-bit key using 600,000 iterations (OWASP standard)."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32, # 256 bits
            salt=salt,
            iterations=600000
        )
        return kdf.derive(password.encode())

    def process(self, encrypt=True, file_path=None):
        path_str = file_path if file_path else filedialog.askopenfilename()
        if not path_str: return
        path = Path(path_str)
        
        pwd = simpledialog.askstring("Auth", "Enter Secure Passcode:", show='*')
        if not pwd: return

        try:
            if encrypt:
                salt, nonce = os.urandom(16), os.urandom(12)
                aesgcm = AESGCM(self.get_key(pwd, salt))
                with open(path, "rb") as f:
                    data = f.read()
                ciphertext = aesgcm.encrypt(nonce, data, None)
                output = salt + nonce + ciphertext
                new_path = path.with_suffix(path.suffix + MY_EXTENSION)
            else:
                with open(path, "rb") as f:
                    data = f.read()
                salt, nonce, ciphertext = data[:16], data[16:28], data[28:]
                aesgcm = AESGCM(self.get_key(pwd, salt))
                output = aesgcm.decrypt(nonce, ciphertext, None)
                new_path = path.with_suffix('')

            with open(new_path, "wb") as f:
                f.write(output)
            os.remove(path)
            messagebox.showinfo("Success", f"File {'Encrypted' if encrypt else 'Decrypted'}!")
        except Exception:
            messagebox.showerror("Security Error", "Incorrect passcode or corrupted data.")

if __name__ == "__main__":
    if sys.platform == "win32" and len(sys.argv) == 1:
        setup_windows_registry()
    root = tk.Tk()
    app = SecureVault(root)
    root.mainloop()
