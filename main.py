import os, sys, shutil, tempfile, threading, zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
import vault_engine as ve

class SecureVault:
    def __init__(self, root):
        self.root = root
        root.title("Secure Crypt")
        root.geometry("420x540")
        
        lf = ("Segoe UI", 16, "bold") if sys.platform == "win32" else ("Helvetica", 16, "bold")
        tk.Label(root, text="Secure Crypt", font=lf).pack(pady=15)
        tk.Label(root, text="AES-256-GCM Encryption Engine", font=("Arial", 8), fg="gray").pack()

        self.force_lock = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Force Password Every Time (Must use Quick View)", variable=self.force_lock, font=("Arial", 9, "bold"), fg="#c0392b").pack(pady=5)

        tk.Button(root, text="⚡ QUICK VIEW FILE (Auto-Relock)", command=lambda: self.qv(False), bg="#d35400", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=60, pady=5)
        tk.Button(root, text="⚡ QUICK VIEW FOLDER (Auto-Relock)", command=lambda: self.qv(True), bg="#e67e22", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=60, pady=5)

        tk.Label(root, text="--- Permanent Tools ---", fg="gray", font=("Arial", 7)).pack(pady=5)
        tk.Button(root, text="🔒 LOCK FILE", command=lambda: self.start(True, False), bg="#2c3e50", fg="white", font=("Arial", 9, "bold")).pack(fill="x", padx=80, pady=2)
        tk.Button(root, text="🔓 UNLOCK FILE", command=lambda: self.start(False, False), bg="#27ae60", fg="white", font=("Arial", 9, "bold")).pack(fill="x", padx=80, pady=2)
        tk.Button(root, text="📂 LOCK FOLDER", command=lambda: self.start(True, True), bg="#34495e", fg="white", font=("Arial", 9)).pack(fill="x", padx=80, pady=2)
        tk.Button(root, text="📂 UNLOCK FOLDER", command=lambda: self.start(False, True), bg="#2ecc71", fg="white", font=("Arial", 9)).pack(fill="x", padx=80, pady=2)

        if sys.platform == "win32":
            ve.reg_assoc()
        self.root.after(100, self.check_args)

    def check_args(self):
        if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
            t = Path(sys.argv[1])
            is_f = t.suffix.lower() == ve.E_FOLD
            self.root.withdraw()
            pwd = simpledialog.askstring("Password Required", f"Enter password to view this {'folder' if is_f else 'file'}:", show='*')
            if pwd: self.proc_qv(t, pwd, is_f, True)
            else: sys.exit(0)

    def qv(self, is_fold):
        ext, msg = (ve.E_FOLD, "Folder") if is_fold else (ve.E_FILE, "File")
        p = filedialog.askopenfilename(filetypes=[(f"Secure {msg}", f"*{ext}")])
        if not p: return
        pwd = simpledialog.askstring("Password Required", f"Enter password to view this {msg.lower()}:", show='*')
        if pwd: threading.Thread(target=self.proc_qv, args=(Path(p), pwd, is_fold), daemon=True).start()

    def proc_qv(self, path, pwd, is_fold, close_on_done=False):
        try:
            with open(path, "rb") as f: data = f.read()
            flag, salt, nonce, cipher = data[:1], data[1:17], data[17:29], data[29:]
            out = ve.crypt(pwd, salt, nonce, cipher, enc=False)
            tdir = tempfile.mkdtemp()
            
            if is_fold:
                zf = os.path.join(tdir, "b.zip")
                with open(zf, "wb") as f: f.write(out)
                t_out = os.path.join(tdir, path.name.replace(ve.E_FOLD, ""))
                os.makedirs(t_out, exist_ok=True)
                with zipfile.ZipFile(zf, 'r') as z: z.extractall(t_out)
                os.remove(zf)
            else:
                t_out = os.path.join(tdir, path.name.replace(ve.E_FILE, ""))
                with open(t_out, "wb") as f: f.write(out)

            ve.open_file(t_out)

            def save_close():
                try:
                    if os.path.exists(t_out):
                        if is_fold:
                            zf = os.path.join(tdir, "nb.zip")
                            ve.zip_dir(t_out, zf)
                            with open(zf, "rb") as f: mdata = f.read()
                        else:
                            with open(t_out, "rb") as f: mdata = f.read()
                        ns, nn = os.urandom(16), os.urandom(12)
                        with open(path, "wb") as f: f.write(flag + ns + nn + ve.crypt(pwd, ns, nn, mdata, enc=True))
                except:
                    messagebox.showerror("Save Error", "Could not save changes. Ensure file is closed.")
                    return
                shutil.rmtree(tdir)
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append('')
                    self.root.update()
                except: pass
                box.destroy()
                messagebox.showinfo("Success", "Changes saved. File re-locked.")
                if close_on_done: sys.exit(0)

            box = tk.Toplevel(self.root)
            box.geometry("340x140")
            box.attributes("-topmost", True)
            box.protocol("WM_DELETE_WINDOW", lambda: [shutil.rmtree(tdir), box.destroy(), sys.exit(0) if close_on_done else None])
            tk.Label(box, text="File opened in temporary view mode.\nYou can make edits directly.\n\n⚠️ IMPORTANT: Save and close application BEFORE clicking below.", font=("Arial", 9, "bold"), fg="#c0392b").pack(pady=10)
            tk.Button(box, text="🔒 SAVE EDITS & RELOCK", command=save_close, bg="#27ae60", fg="white", font=("Arial", 9, "bold")).pack(pady=5)
        except:
            messagebox.showerror("Decryption Error", "Incorrect password or corrupted data.")
            if close_on_done: sys.exit(0)

    def start(self, enc, is_f):
        p = filedialog.askopenfilename(filetypes=[("Secure Folders", f"*{ve.E_FOLD}")]) if (not enc and is_f) else (filedialog.askdirectory() if is_f else filedialog.askopenfilename())
        if not p: return
        if not enc:
            try:
                with open(p, "rb") as f:
                    flag = f.read(1); f.seek(0)
                    if flag == b'M': return messagebox.showerror("Access Denied", "Mandatory lock. Use Quick View.")
            except: pass
        pwd = simpledialog.askstring("Password Required", "Enter password:")
        if not pwd or (enc and pwd != simpledialog.askstring("Confirm Password", "Confirm password:", show='*')): return
        pop = tk.Toplevel(self.root); pop.geometry("300x100"); pop.title("Processing...")
        pb = ttk.Progressbar(pop, orient="horizontal", length=240, mode="indeterminate")
        pb.pack(pady=30)
        threading.Thread(target=ve.run_task, args=(enc, p, pwd, pop, is_f, self.force_lock.get()), daemon=True).start()

if __name__ == "__main__":
    r = tk.Tk(); app = SecureVault(r); r.mainloop()
