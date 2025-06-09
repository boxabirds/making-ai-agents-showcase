#!/bin/bash

# Installation script for Open-CUAK package using Homebrew (package form)

# Client and Server combined as the instructions indicate starting services after installation

# Step 1: (Optional) Install Homebrew package manager if not already installed
if ! command -v brew &> /dev/null
then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Register brew in shell environment for Linux if needed
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        test -d ~/.linuxbrew && eval "$(~/.linuxbrew/bin/brew shellenv)"
        test -d /home/linuxbrew/.linuxbrew && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        echo "eval \"\$($(brew --prefix)/bin/brew shellenv)\"" >> ~/.bashrc
    fi
    echo "Homebrew installed."
else
    echo "Homebrew already installed."
fi

# Step 2: Install or update Open-CUAK package via Homebrew
echo "Installing or updating Open-CUAK package..."
brew install Aident-AI/homebrew-tap/open-cuak || brew upgrade Aident-AI/homebrew-tap/open-cuak

# Step 3: Start Open-CUAK services
echo "Starting Open-CUAK services (this may take some time to download images)..."
open-cuak start

# Step 4: Inform user of local access URL and configuration reminder
echo "Open-CUAK is now ready locally at http://localhost:11970"
echo "Don't forget to go to the ⚙️ Configurations page to set your OpenAI or other major model API key to chat with Aiden!"