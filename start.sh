#!/bin/bash

# Define project and function names
PROJECT_NAME="lamatodo_be"
FUNCTION_ONE="functionOne"
FUNCTION_TWO="functionTwo"

# Create project directory
mkdir $PROJECT_NAME
cd $PROJECT_NAME

# Create function directories and files
mkdir $FUNCTION_ONE $FUNCTION_TWO
echo "exports.handler = (req, res) => { res.send('Hello from $FUNCTION_ONE'); }" > $FUNCTION_ONE/index.js
echo "exports.handler = (req, res) => { res.send('Hello from $FUNCTION_TWO'); }" > $FUNCTION_TWO/index.js
echo "{}" > $FUNCTION_ONE/package.json
echo "{}" > $FUNCTION_TWO/package.json

# Create shared library directory
mkdir lib
echo "// Shared utility functions" > lib/utility.js

# Create test directory and files
mkdir test
echo "// Tests for $FUNCTION_ONE" > test/$FUNCTION_ONE.test.js
echo "// Tests for $FUNCTION_TWO" > test/$FUNCTION_TWO.test.js

# Create environment files
echo "ENV=production" > .env.production
echo "ENV=development" > .env.development

# Create README and .gitignore
echo "# $PROJECT_NAME" > README.md
echo "node_modules/" > .gitignore
echo ".env*" >> .gitignore

# Message
echo "Project structure for $PROJECT_NAME created successfully."
