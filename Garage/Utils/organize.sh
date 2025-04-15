#!/bin/bash

# List Python files
echo "Python files found:"
find . -maxdepth 1 -name "*.py" | sort

# Ask for each file where it should go
for file in $(find . -maxdepth 1 -name "*.py" -type f); do
  if [[ "$file" != "./organize.sh" ]]; then
    echo "=============================="
    echo "File: $file"
    echo "Content preview:"
    head -n 10 "$file"
    echo "=============================="
    echo "Where should this file go? (UI/Core/Utils/Config/Models/Skip)"
    read destination
    if [[ "$destination" != "Skip" ]]; then
      mv "$file" "./Garage/${destination}/"
      echo "Moved to ./Garage/${destination}/"
    else
      echo "Skipped"
    fi
  fi
done

# Handle non-Python files
echo "=============================="
echo "Non-Python files:"
find . -maxdepth 1 -type f -not -name "*.py" -not -name "organize.sh" | sort

echo "=============================="
echo "Where should these go? (UI/Core/Utils/Config/Models/Skip)"
read destination
if [[ "$destination" != "Skip" ]]; then
  find . -maxdepth 1 -type f -not -name "*.py" -not -name "organize.sh" -exec mv {} "./Garage/${destination}/" \;
  echo "Moved to ./Garage/${destination}/"
else
  echo "Skipped"
fi
