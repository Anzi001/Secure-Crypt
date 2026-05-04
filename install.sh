#!/bin/bash
if [[ "$OSTYPE" == "darwin"* ]]; then
    URL="https://github.com"
    echo "Downloading for Mac..."
    curl -L $URL -o ~/Desktop/Encrypter.zip
    unzip ~/Desktop/Encrypter.zip -d ~/Desktop/
    rm ~/Desktop/Encrypter.zip
else
    URL="https://github.com"
    echo "Downloading for Linux..."
    curl -L $URL -o ~/Desktop/FileEncrypter
    chmod +x ~/Desktop/FileEncrypter
fi
echo "Installation complete! Check your Desktop."
