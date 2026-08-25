param(
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
$ExpectedLabel = 'revisionproof-repo'
$Containers = @(
    'revisionproof-local-qa-20260825',
    'revisionproof-foundation-qa-20260825'
)
$Images = @(
    'revisionproof:qa-hardening',
    'revisionproof:foundation'
)

function Get-ManagedByLabel {
    param(
        [Parameter(Mandatory)]
        [string]$Target
    )

    $inspectionJson = & docker inspect $Target 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    $inspection = $inspectionJson | ConvertFrom-Json
    return $inspection[0].Config.Labels.'com.kanapp.managed-by'
}

Write-Host 'RevisionProof-only Docker cleanup plan:'
foreach ($container in $Containers) {
    $label = Get-ManagedByLabel -Target $container
    if ($null -eq $label) {
        Write-Host "  absent container: $container"
        continue
    }
    if ($label -ne $ExpectedLabel) {
        throw "Refusing container ${container}: managed-by label is '$label'."
    }
    Write-Host "  container: $container"
}
foreach ($image in $Images) {
    $label = Get-ManagedByLabel -Target $image
    if ($null -eq $label) {
        Write-Host "  absent image: $image"
        continue
    }
    if ($label -ne $ExpectedLabel) {
        throw "Refusing image ${image}: managed-by label is '$label'."
    }
    Write-Host "  image: $image"
}

if (-not $Execute) {
    Write-Host 'Dry run only. Re-run with -Execute after reviewing the exact targets.'
    exit 0
}

foreach ($container in $Containers) {
    if ($null -eq (Get-ManagedByLabel -Target $container)) {
        continue
    }
    $running = & docker inspect --format '{{.State.Running}}' $container
    if ($running -eq 'true') {
        & docker stop $container
    }
    & docker container rm $container
}
foreach ($image in $Images) {
    if ($null -ne (Get-ManagedByLabel -Target $image)) {
        & docker image rm $image
    }
}
