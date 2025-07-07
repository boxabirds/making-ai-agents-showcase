#!/bin/bash

# Dependency Checker for Tech Writer Implementations
# Checks for required binaries and provides installation instructions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        elif [ -f /etc/arch-release ]; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)

echo "=== Tech Writer Dependency Checker ==="
echo "Detected OS: $OS"
echo ""

# Function to check if a command exists
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to get version
get_version() {
    local cmd=$1
    local version_flag=$2
    if check_command "$cmd"; then
        $cmd $version_flag 2>&1 | head -n 1
    else
        echo "Not installed"
    fi
}

# Installation instructions based on OS
provide_install_instructions() {
    local tool=$1
    echo -e "${YELLOW}Installation instructions for $tool:${NC}"
    
    case $tool in
        "PHP")
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install php"
                    echo "  macOS (MacPorts): sudo port install php84"
                    ;;
                "debian")
                    echo "  Debian/Ubuntu: sudo apt update && sudo apt install php-cli php-curl php-mbstring"
                    ;;
                "redhat")
                    echo "  RHEL/CentOS/Fedora: sudo dnf install php-cli php-curl php-mbstring"
                    ;;
                "arch")
                    echo "  Arch Linux: sudo pacman -S php"
                    ;;
                "windows")
                    echo "  Windows: Download from https://windows.php.net/download/"
                    echo "  Or use Chocolatey: choco install php"
                    ;;
                *)
                    echo "  Visit: https://www.php.net/manual/en/install.php"
                    ;;
            esac
            ;;
            
        "Composer")
            echo "  All platforms: "
            echo "  curl -sS https://getcomposer.org/installer | php"
            echo "  sudo mv composer.phar /usr/local/bin/composer"
            echo ""
            echo "  Or visit: https://getcomposer.org/download/"
            ;;
            
        "Go")
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install go"
                    echo "  macOS (MacPorts): sudo port install go"
                    ;;
                "debian")
                    echo "  Debian/Ubuntu: sudo apt update && sudo apt install golang-go"
                    ;;
                "redhat")
                    echo "  RHEL/CentOS/Fedora: sudo dnf install golang"
                    ;;
                "arch")
                    echo "  Arch Linux: sudo pacman -S go"
                    ;;
                "windows")
                    echo "  Windows: Download from https://go.dev/dl/"
                    echo "  Or use Chocolatey: choco install golang"
                    ;;
                *)
                    echo "  Visit: https://go.dev/doc/install"
                    ;;
            esac
            ;;
            
        "Bun")
            echo "  All platforms (recommended):"
            echo "  curl -fsSL https://bun.sh/install | bash"
            echo ""
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install oven-sh/bun/bun"
                    ;;
                "windows")
                    echo "  Windows: Use WSL or download from https://bun.sh"
                    ;;
            esac
            echo "  Visit: https://bun.sh"
            ;;
            
        "Node.js")
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install node"
                    echo "  macOS (MacPorts): sudo port install nodejs20"
                    ;;
                "debian")
                    echo "  Debian/Ubuntu: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
                    echo "                 sudo apt install nodejs"
                    ;;
                "redhat")
                    echo "  RHEL/CentOS/Fedora: sudo dnf install nodejs"
                    ;;
                "arch")
                    echo "  Arch Linux: sudo pacman -S nodejs npm"
                    ;;
                "windows")
                    echo "  Windows: Download from https://nodejs.org/"
                    echo "  Or use Chocolatey: choco install nodejs"
                    ;;
                *)
                    echo "  Visit: https://nodejs.org/"
                    ;;
            esac
            ;;
            
        "Rust")
            echo "  All platforms (recommended):"
            echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            echo ""
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install rust"
                    ;;
                "windows")
                    echo "  Windows: Download from https://rustup.rs/"
                    ;;
            esac
            echo "  Visit: https://www.rust-lang.org/tools/install"
            ;;
            
        "C Compiler")
            case $OS in
                "macos")
                    echo "  macOS: Xcode Command Line Tools are usually pre-installed"
                    echo "  Install with: xcode-select --install"
                    echo "  Or Homebrew: brew install gcc"
                    ;;
                "debian")
                    echo "  Debian/Ubuntu: sudo apt update && sudo apt install build-essential"
                    ;;
                "redhat")
                    echo "  RHEL/CentOS/Fedora: sudo dnf install gcc make"
                    ;;
                "arch")
                    echo "  Arch Linux: sudo pacman -S base-devel"
                    ;;
                "windows")
                    echo "  Windows: Install Visual Studio with C++ development tools"
                    echo "  Or MinGW: https://www.mingw-w64.org/"
                    ;;
            esac
            ;;
            
        "libcurl")
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install curl"
                    echo "  Note: macOS includes libcurl by default"
                    ;;
                "debian")
                    echo "  Debian/Ubuntu: sudo apt update && sudo apt install libcurl4-openssl-dev"
                    ;;
                "redhat")
                    echo "  RHEL/CentOS/Fedora: sudo dnf install libcurl-devel"
                    ;;
                "arch")
                    echo "  Arch Linux: sudo pacman -S curl"
                    ;;
                "windows")
                    echo "  Windows: Download from https://curl.se/windows/"
                    echo "  Or use vcpkg: vcpkg install curl"
                    ;;
            esac
            ;;
            
        "Zig")
            echo "  All platforms (recommended):"
            echo "  curl -L https://ziglang.org/download/0.12.0/zig-linux-x86_64-0.12.0.tar.xz | tar xJ"
            echo "  export PATH=\"\$PATH:/path/to/zig\""
            echo ""
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install zig"
                    echo "  macOS (MacPorts): sudo port install zig"
                    ;;
                "windows")
                    echo "  Windows: Download from https://ziglang.org/download/"
                    echo "  Or use Chocolatey: choco install zig"
                    ;;
            esac
            echo "  Visit: https://ziglang.org/download/"
            ;;
            
        "Python")
            case $OS in
                "macos")
                    echo "  macOS (Homebrew): brew install python@3.12"
                    echo "  macOS (MacPorts): sudo port install python312"
                    ;;
                "debian")
                    echo "  Debian/Ubuntu: sudo apt update && sudo apt install python3 python3-pip python3-venv"
                    ;;
                "redhat")
                    echo "  RHEL/CentOS/Fedora: sudo dnf install python3 python3-pip"
                    ;;
                "arch")
                    echo "  Arch Linux: sudo pacman -S python python-pip"
                    ;;
                "windows")
                    echo "  Windows: Download from https://www.python.org/downloads/"
                    echo "  Or use Chocolatey: choco install python"
                    ;;
                *)
                    echo "  Visit: https://www.python.org/downloads/"
                    ;;
            esac
            ;;
    esac
    echo ""
}

# Check each dependency
echo "Checking dependencies..."
echo ""

# PHP
echo -n "PHP: "
if check_command php; then
    echo -e "${GREEN}✓${NC} $(get_version php --version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "PHP"
fi

# Composer
echo -n "Composer: "
if check_command composer; then
    echo -e "${GREEN}✓${NC} $(get_version composer --version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "Composer"
fi

# Go
echo -n "Go: "
if check_command go; then
    echo -e "${GREEN}✓${NC} $(get_version go version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "Go"
fi

# Bun (for TypeScript)
echo -n "Bun: "
if check_command bun; then
    echo -e "${GREEN}✓${NC} $(get_version bun --version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "Bun"
    
    # If Bun is not installed, check for Node.js as alternative
    echo -n "Node.js (alternative): "
    if check_command node; then
        echo -e "${GREEN}✓${NC} $(get_version node --version)"
        echo -n "TypeScript: "
        if check_command tsc; then
            echo -e "${GREEN}✓${NC} $(get_version tsc --version)"
        else
            echo -e "${YELLOW}!${NC} Node.js installed but TypeScript not found"
            echo "  Install TypeScript: npm install -g typescript"
        fi
    else
        echo -e "${RED}✗${NC} Not installed"
        provide_install_instructions "Node.js"
    fi
fi

# Rust
echo -n "Rust/Cargo: "
if check_command cargo; then
    echo -e "${GREEN}✓${NC} $(get_version cargo --version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "Rust"
fi

# C Compiler and libcurl
echo -n "C Compiler (cc/gcc): "
if check_command cc || check_command gcc; then
    if check_command cc; then
        echo -e "${GREEN}✓${NC} $(cc --version 2>&1 | head -n 1)"
    else
        echo -e "${GREEN}✓${NC} $(gcc --version | head -n 1)"
    fi
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "C Compiler"
fi

echo -n "libcurl: "
if pkg-config --exists libcurl 2>/dev/null || [ -f /usr/include/curl/curl.h ] || [ -f /usr/local/include/curl/curl.h ] || [ -f /opt/homebrew/include/curl/curl.h ]; then
    if pkg-config --exists libcurl 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $(pkg-config --modversion libcurl)"
    else
        echo -e "${GREEN}✓${NC} Installed (header found)"
    fi
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "libcurl"
fi

# Zig
echo -n "Zig: "
if check_command zig; then
    echo -e "${GREEN}✓${NC} $(get_version zig version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "Zig"
fi

# Python
echo -n "Python3: "
if check_command python3; then
    echo -e "${GREEN}✓${NC} $(get_version python3 --version)"
else
    echo -e "${RED}✗${NC} Not installed"
    provide_install_instructions "Python"
fi

# Git (required for all implementations)
echo -n "Git: "
if check_command git; then
    echo -e "${GREEN}✓${NC} $(get_version git --version)"
else
    echo -e "${RED}✗${NC} Not installed"
    echo -e "${YELLOW}Git is required for all implementations!${NC}"
    case $OS in
        "macos")
            echo "  macOS: xcode-select --install"
            echo "  Or Homebrew: brew install git"
            ;;
        "debian")
            echo "  Debian/Ubuntu: sudo apt update && sudo apt install git"
            ;;
        "redhat")
            echo "  RHEL/CentOS/Fedora: sudo dnf install git"
            ;;
        "arch")
            echo "  Arch Linux: sudo pacman -S git"
            ;;
        "windows")
            echo "  Windows: Download from https://git-scm.com/download/win"
            echo "  Or use Chocolatey: choco install git"
            ;;
    esac
fi

echo ""
echo "=== Summary ==="

# Count missing dependencies
missing=0
[ ! -x "$(command -v php)" ] && ((missing++))
[ ! -x "$(command -v composer)" ] && ((missing++))
[ ! -x "$(command -v go)" ] && ((missing++))
[ ! -x "$(command -v bun)" ] && [ ! -x "$(command -v node)" ] && ((missing++))
[ ! -x "$(command -v cargo)" ] && ((missing++))
[ ! -x "$(command -v cc)" ] && [ ! -x "$(command -v gcc)" ] && ((missing++))
if ! pkg-config --exists libcurl 2>/dev/null && [ ! -f /usr/include/curl/curl.h ] && [ ! -f /usr/local/include/curl/curl.h ] && [ ! -f /opt/homebrew/include/curl/curl.h ]; then
    ((missing++))
fi
[ ! -x "$(command -v zig)" ] && ((missing++))
[ ! -x "$(command -v python3)" ] && ((missing++))
[ ! -x "$(command -v git)" ] && ((missing++))

if [ $missing -eq 0 ]; then
    echo -e "${GREEN}All dependencies are installed!${NC}"
    echo "You can run any of the tech writer implementations."
else
    echo -e "${YELLOW}Missing $missing dependencies.${NC}"
    echo "Install the missing dependencies above to run the corresponding implementations."
fi

# Check for GNU coreutils on macOS (for eval script)
if [[ "$OS" == "macos" ]]; then
    echo ""
    echo -n "GNU coreutils (for eval script): "
    if check_command gtimeout; then
        echo -e "${GREEN}✓${NC} Installed"
    else
        echo -e "${YELLOW}!${NC} Not installed"
        echo "  The eval script requires GNU coreutils on macOS"
        echo "  Install with: brew install coreutils"
    fi
fi