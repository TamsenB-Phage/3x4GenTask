# Windows Setup Guide

This project is developed on macOS/Linux using `make` and Conda.  
On Windows, the recommended approach is to use **WSL (Windows Subsystem for Linux)**.

---

## ✅ Recommended: Use WSL

WSL provides a Linux environment where the project runs exactly as intended.

### 1. Install WSL

Open PowerShell as Administrator:

```bash
wsl --install
```
Restart your machine if prompted.

### 2. Install Miniconda (inside WSL)

In the WSL terminal:
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```
Restart the shell, then verify:
```bash
conda --version
```

### 3. Install make

```bash
sudo apt update
sudo apt install make
```

### 4. Run the pipeline

From the repository root:

```bash
make setup-all
make process
make report
make recovery   # optional (experimental)
```

## ⚙️ Alternative: Native Windows

Running without WSL is possible but less reliable.

**Requirements**
- Miniconda (Windows)
- Git Bash or PowerShell
- make (via Git Bash or Chocolatey)

Install `make` with Chocolatey if needed:

```PowerShell
choco install make
```

Then run:

```bash
make setup-all
make process
make report
make recovery
```

## ⚠️ Notes
- The project uses pathlib and is cross-platform compatible
- Expected directory structure:

```
repo/
workouts/   # input (.fit files)
out/        # generated outputs
```
Place your `.fit` files in `workouts/` before running the pipeline

## 💡 Recommendation

For development and reproducibility:

Use WSL — it avoids most Windows-specific issues.