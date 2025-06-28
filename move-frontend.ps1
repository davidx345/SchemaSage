# PowerShell script to move the frontend folder to a new location and print next steps

# Set source and destination paths
$Source = "${PSScriptRoot}\frontend"
$Destination = "${PSScriptRoot}\..\schemasage-frontend"

# Copy the frontend folder to the new location
Write-Host "Copying frontend to $Destination ..."
Copy-Item -Path $Source -Destination $Destination -Recurse -Force

# Check if copy succeeded
if (Test-Path $Destination) {
    Write-Host "Copy successful!"
    # Optionally remove the original folder (uncomment to enable)
    # Remove-Item -Path $Source -Recurse -Force
    Write-Host "\nNext steps:"
    Write-Host "1. Verify the new frontend at: $Destination"
    Write-Host "2. Update your frontend .env to set NEXT_PUBLIC_API_URL to your API Gateway URL (e.g., http://localhost:8000)"
    Write-Host "3. Update CORS settings in your API Gateway to allow the new frontend domain if deploying remotely."
    Write-Host "4. Remove the original frontend folder when you are sure everything works."
    Write-Host "5. (Optional) Initialize a new git repository in the new frontend folder."
} else {
    Write-Host "Copy failed! Please check permissions and paths."
}
