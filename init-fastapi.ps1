# Define root path
$projectRoot = "C:\Users\USER-Q\Desktop\FastAPI-CMS\fastApiProject2"
$appPath = Join-Path $projectRoot "app"

# Create main project folder and app folder
New-Item -ItemType Directory -Force -Path $projectRoot
New-Item -ItemType Directory -Force -Path $appPath

# Define folders inside "app"
$folders = @("core", "models", "schemas", "crud", "api", "services", "tasks", "media", "alembic")

# Create folders
foreach ($folder in $folders) {
    $path = Join-Path $appPath $folder
    New-Item -ItemType Directory -Force -Path $path | Out-Null

    # Create __init__.py inside each subfolder
    New-Item -ItemType File -Path (Join-Path $path "__init__.py") -Force | Out-Null
}

# Create top-level files
$topLevelFiles = @("main.py", "__init__.py", "requirements.txt", "README.md")
foreach ($file in $topLevelFiles) {
    New-Item -ItemType File -Path (Join-Path $appPath $file) -Force | Out-Null
}

Write-Host "✅ FastAPI folder structure initialized at $projectRoot"
