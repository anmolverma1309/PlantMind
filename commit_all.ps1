# Get all files recursively, excluding node_modules, venv, and .git directories
$files = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch 'node_modules|venv|\.git' }

Write-Host "Found $($files.Count) files to commit."

$count = 0
foreach ($file in $files) {
    $relativePath = Resolve-Path -Relative $file.FullName
    
    # Check if the file is ignored by git
    git check-ignore -q $relativePath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Skipping ignored file: $relativePath"
        continue
    }
    
    $count++
    Write-Host "Committing [$count/$($files.Count)]: $relativePath"
    
    # Stage the file
    git add $relativePath
    
    # Commit the file
    git commit -m "Add $relativePath"
}

Write-Host "Completed committing $count files separately."
