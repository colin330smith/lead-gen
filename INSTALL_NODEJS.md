# Installing Node.js for Local Lift

**You need Node.js to run the frontend. Here's how to install it on macOS:**

---

## 🍺 Option 1: Install via Homebrew (Recommended)

### Step 1: Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Node.js
```bash
brew install node
```

### Step 3: Verify Installation
```bash
node --version  # Should show v18.x.x or higher
npm --version   # Should show 9.x.x or higher
```

---

## 📦 Option 2: Install via Official Installer

1. **Download Node.js:**
   - Visit: https://nodejs.org/
   - Download the LTS version (v18 or v20)
   - Choose the macOS installer (.pkg file)

2. **Run the installer:**
   - Double-click the downloaded .pkg file
   - Follow the installation wizard
   - Complete the installation

3. **Verify Installation:**
   ```bash
   node --version
   npm --version
   ```

---

## 🔧 Option 3: Install via nvm (Node Version Manager)

### Step 1: Install nvm
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
```

### Step 2: Reload your shell
```bash
source ~/.zshrc  # or ~/.bash_profile
```

### Step 3: Install Node.js
```bash
nvm install 18
nvm use 18
```

### Step 4: Verify
```bash
node --version
npm --version
```

---

## ✅ After Installation

Once Node.js is installed, you can proceed with the frontend setup:

```bash
cd /Users/colinsmith/local-lift/frontend
npm install
npm run dev
```

---

## 🚨 Troubleshooting

### If `npm` still not found after installation:
1. **Close and reopen your terminal**
2. **Reload your shell profile:**
   ```bash
   source ~/.zshrc
   ```
3. **Check your PATH:**
   ```bash
   echo $PATH
   ```
   Should include `/usr/local/bin` or `~/.nvm/versions/node/...`

### If using Homebrew and still having issues:
```bash
# Add Homebrew to PATH (if needed)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

---

**Once Node.js is installed, return to the main setup guide!**

