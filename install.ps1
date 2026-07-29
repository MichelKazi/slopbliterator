$ErrorActionPreference = "Stop"

if ($PSScriptRoot) {
    $localInstaller = Join-Path $PSScriptRoot "bin/install.js"
    if (Test-Path $localInstaller) {
        & node $localInstaller @args
        exit $LASTEXITCODE
    }
}

& npx -y github:MichelKazi/slopbliterator @args
exit $LASTEXITCODE
