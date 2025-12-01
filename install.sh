#!/bin/bash
# Unix shell script to run the dependency installation script

echo "Running dependency installation script..."
python3 install_dependencies.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation encountered errors. Please check the output above."
    exit 1
fi

echo ""
echo "Installation completed successfully!"
