Write-Output 'Checking processes listening on port 8000...'
$owningPids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($owningPids -and ($owningPids.Count -gt 0)) {
  foreach ($ownPid in $owningPids) {
    try { Stop-Process -Id $ownPid -Force -ErrorAction SilentlyContinue; Write-Output ("Stopped PID {0}" -f $ownPid) } catch { Write-Output ("Failed to stop PID {0}: {1}" -f $ownPid, $_) }
  }
} else {
  Write-Output 'No process listening on port 8000.'
}

Write-Output 'Also scanning Python processes with app.py or flask in command line...'
$matches = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'flask|app.py') }
if ($matches) {
  foreach ($m in $matches) {
    try { Stop-Process -Id $m.ProcessId -Force -ErrorAction SilentlyContinue; Write-Output ("Stopped PID {0} (matched command)" -f $m.ProcessId) } catch { Write-Output ("Failed to stop PID {0}: {1}" -f $m.ProcessId, $_) }
  }
} else {
  Write-Output 'No matching python/flask processes found.'
}
