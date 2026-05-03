import os, sys, base64
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from pathlib import Path

# --- CONFIGURATION ---
MY_EXTENSION = ".locked"
PROG_NAME = "File Encrypter"

def setup_os_integration():
    """Handles OS-specific setup. Skipped on Mac as it requires bundle packaging."""
    if sys.platform == "win32":
        try:
            import ctypes
            import winreg
            
            # Check for admin
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            flag_file = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'FileEncrypter_initialized.dat')
            
            if not os.path.exists(flag_file):
                if not is_admin:
                    # Request elevation
                    params = f'"{os.path.abspath(sys.argv[0])}"'
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                    sys.exit()
                else:
                    # Register Windows Registry
                    script_path = os.path.abspath(sys.argv[0])
                    app_path = sys.executable if getattr(sys, 'frozen', False) else script_path
                    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, MY_EXTENSION) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, "LockedFile")
                    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"LockedFile\shell\open\command") as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f'"{app_path}" "%1"')
                    with open(flag_file, 'w') as f: f.write('initialized')
        except Exception as e:
            print(f"OS Integration failed: {e}")

class SecureVault:
    def __init__(self, root):
        self.root = root
        self.root.title(PROG_NAME)
        self.root.geometry("400x250")
        self.root.minsize(300, 200)

        # Standard Tkinter colors for better Mac/Win compatibility
        btn_bg = "#4a90e2" if sys.platform == "win32" else None # Mac buttons don't like custom BG colors in standard TK

        self.root.columnconfigure(0, weight=1)
        for i in range(3): self.root.rowconfigure(i, weight=1)

        self.main_label = tk.Label(root, text=PROG_NAME, font=("Arial", 14, "bold"))
        self.main_label.grid(row=0, column=0, sticky="nsew")

        self.lock_btn = tk.Button(root, text="🔒 Lock File", command=lambda: self.process(True), bg="#4a90e2")
        self.lock_btn.grid(row=1, column=0, sticky="nsew", padx=40, pady=10)

        self.unlock_btn = tk.Button(root, text="🔓 Unlock File", command=lambda: self.process(False), bg="#5cb85c")
        self.unlock_btn.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)

        self.root.bind("<Configure>", self.resize_widgets)

        if len(sys.argv) > 1 and sys.argv[1].endswith(MY_EXTENSION):
            self.root.after(500, lambda: self.process(encrypt=False, file_path=sys.argv[1]))

    def resize_widgets(self, event):
        size = max(10, int(event.height / 18))
        self.main_label.config(font=("Arial", size, "bold"))

    def get_key(self, password, salt):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def process(self, encrypt=True, file_path=None):
        path_str = file_path if file_path else filedialog.askopenfilename()
        if not path_str: return
        path = Path(path_str)
        
        pwd = simpledialog.askstring("Passcode", "Enter passcode:", show='*')
        if not pwd: return

        try:
            if encrypt:
                salt = os.urandom(16)
                fernet = Fernet(self.get_key(pwd, salt))
                with open(path, "rb") as f: data = f.read()
                encrypted_data = salt + fernet.encrypt(data)
                new_path = path.with_suffix(path.suffix + MY_EXTENSION)
            else:
                with open(path, "rb") as f: data = f.read()
                salt, actual_data = data[:16], data[16:]
                fernet = Fernet(self.get_key(pwd, salt))
                decrypted_data = fernet.decrypt(actual_data)
                new_path = path.with_suffix('')

            with open(new_path, "wb") as f: 
                f.write(encrypted_data if encrypt else decrypted_data)
            
            os.remove(path)
            messagebox.showinfo("Done", "Success!")
        except Exception as e: 
            messagebox.showerror("Error", f"Failed: {e}")

if __name__ == "__main__":
    setup_os_integration()
    root = tk.Tk()
    app = SecureVault(root)
    root.mainloop()
