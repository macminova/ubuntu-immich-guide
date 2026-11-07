param(
 [string]$Root=(Split-Path $PSScriptRoot -Parent),
 [string]$DenylistPath=''
)
$ErrorActionPreference='Stop'
$resolved=[IO.Path]::GetFullPath($Root)
if(!(Test-Path -LiteralPath $resolved -PathType Container)){throw 'Root is not a directory'}
if((Get-Item -LiteralPath $resolved -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse point root rejected'}
$items=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
if(@($items|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Reparse point found: review manually'}
$files=@($items|Where-Object {!$_.PSIsContainer -and $_.FullName -notmatch '[\\/]\.git[\\/]'})
$deny=@()
if($DenylistPath){$deny=@(Get-Content -LiteralPath $DenylistPath|Where-Object {$_.Trim() -and ! $_.StartsWith('#')})}
$issues=New-Object 'System.Collections.Generic.List[string]'
foreach($file in $files){
 $relative=$file.FullName.Substring($resolved.Length+1)
 if($file.Name -eq '.env' -or ($file.Name -like '.env.*' -and $file.Name -ne '.env.example') -or $file.Extension -in '.pem','.key','.pfx','.p12','.sql','.dump','.zip','.gz','.jpg','.jpeg','.png','.heic','.mp4','.mov' -or $file.Name -match '^(id_rsa|id_ed25519|known_hosts|authorized_keys)'){$issues.Add("${relative}: forbidden file type/name");continue}
 if($file.Length -gt 524288){$issues.Add("${relative}: large file needs review");continue}
 $lines=[IO.File]::ReadAllLines($file.FullName)
 for($i=0;$i -lt $lines.Length;$i++){
  $line=$lines[$i];$label=$relative+':'+($i+1)
  if($line -match '-----BEGIN [A-Z ]*PRIVATE KEY-----' -or $line -match '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|tskey-[A-Za-z0-9-]{16,})'){$issues.Add("${label}: credential pattern")}
  if($line -match '\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b' -or $line -match '[A-Za-z0-9.-]+\.ts\.net\b'){$issues.Add("${label}: private endpoint pattern")}
  if($line -match '(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s]+'){$issues.Add("${label}: personal home path")}
  if($line -match '(?i)^\s*(DB_PASSWORD|API_KEY|ACCESS_TOKEN|CLIENT_SECRET)\s*=\s*(\S+)'){
   if($Matches[2] -notmatch '^__SET_[A-Z_]+__$' -and $Matches[2] -notmatch '^\$\{[A-Z_]+\}$'){$issues.Add("${label}: non-placeholder credential assignment")}
  }
  foreach($value in $deny){if($line.IndexOf($value,[StringComparison]::OrdinalIgnoreCase) -ge 0){$issues.Add("${label}: private denylist match");break}}
 }
}
if($issues.Count){$issues|Write-Output;Write-Output ('FAIL: '+$issues.Count+' findings');exit 1}
Write-Output ('PASS: '+$files.Count+' files checked; no configured patterns found. Manual review and Git history review still required.')
exit 0
