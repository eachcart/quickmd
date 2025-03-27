# QuickMD

> A simple and easy-to-use utility to create, verify and edit protected `.qmd` files using AES encryption.

## ✨ Possibilities

- ✅ Checking file integrity with `.qmd`
- 🔐 Encrypting files with unique keys
- 🛠 Create and edit `.qmd` files
- 🧰 Built-in file manager
- 📜 Uses AES (EAX) for strong data protection
- 🗝 Two key generation:
    - **Verification Key** for verification
    - **Full Decryption Key** - for decryption.

## 📦 Run on Linux
```bash
git clone https://github.com/eachcart/quickmd.git
cd quickmd
pip install -r quickmd.pyreq
python3 main.py
```

## 📦 Building & Run on Windows
```bash
git clone https://github.com/eachcart/quickmd.git
cd quickmd 
pyinstaller --onefile --noconsole --icon=icon.ico main.py
```
or just download the assembled image of the program in the release, or the portable version.
