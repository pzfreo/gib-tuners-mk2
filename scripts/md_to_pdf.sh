#!/bin/bash

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null
then
    echo "Error: pandoc is not installed. Please install it to use this script."
    exit 1
fi

# Iterate over all .md files in the current directory
for file in *.md; do
    # Check if any .md files exist to avoid processing the literal "*.md"
    [ -e "$file" ] || continue
    
    # Get the filename without extension
    filename="${file%.*}"
    
    echo "Converting $file to ${filename}.pdf..."
    
    # Run pandoc conversion
    # Note: This assumes a PDF engine like pdflatex, tectonic, or wkhtmltopdf is installed.
    pandoc "$file" -o "${filename}.pdf"
    
    if [ $? -eq 0 ]; then
        echo "Successfully converted $file"
    else
        echo "Failed to convert $file"
    fi
done
