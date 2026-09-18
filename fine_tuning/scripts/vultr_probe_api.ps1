# One-shot probe: Vultr API key + IP allowlist. Does not print the key.
param(
    [int]$TimeoutMinutes = 0,
    [int]$IntervalSec = 30
)

. "$PSScriptRoot\vultr_common.ps1"

function Get-AgentPublicIp {
    try {
        return (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 15).ToString().Trim()
    }
    catch {
        return "unknown"
    }
}

$ip = Get-AgentPublicIp
Write-Host "agent_public_ip=$ip"
Write-Host "Allowlist this IP on the Vultr API key if GET /v2/account returns 401."

$deadline = [datetime]::UtcNow.AddMinutes([Math]::Max(0, $TimeoutMinutes))
while ($true) {
    try {
        $acct = Test-VultrApi
        $email = $null
        if ($acct.account -and $acct.account.email) { $email = [string]$acct.account.email }
        Write-Host "Vultr API OK"
        if ($email) { Write-Host "account_email_set=1" }
        exit 0
    }
    catch {
        Write-Host $_.Exception.Message
        if ($TimeoutMinutes -le 0 -or [datetime]::UtcNow -ge $deadline) {
            Write-Host "Vultr API still blocked. Dashboard: Account -> API -> allowlist $ip (or create the GPU VM in console and pass -SshHost)."
            exit 2
        }
        Write-Host "Retrying in ${IntervalSec}s until $($deadline.ToString('u')) ..."
        Start-Sleep -Seconds $IntervalSec
    }
}
