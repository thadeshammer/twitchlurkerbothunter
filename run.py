import sys
import os
import glob

print("Module search paths:", sys.path)
print("Current working directory:", os.getcwd())

print("Directory contents:", os.listdir('/app'))

# Verify the presence of the app module
if os.path.exists('/app/app'):
    print("app directory exists")
    print("app directory contents:", os.listdir('/app/app'))
else:
    print("app directory does not exist")

# Print the contents of app/__init__.py
try:
    with open('/app/app/__init__.py', 'r') as f:
        print("app/__init__.py contents:")
        print(f.read())
except Exception as e:
    print(f"Error reading app/__init__.py: {e}")

try:
    from app import create_app
    print("Import successful")
except ImportError as e:
    print(f"Error importing create_app from app: {e}")

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
