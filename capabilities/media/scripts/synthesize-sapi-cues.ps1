param(
  [Parameter(Mandatory=$true)][string]$InputJson,
  [Parameter(Mandatory=$true)][string]$OutputDir,
  [string]$Voice = 'Microsoft Zira Desktop',
  [int]$Rate = 1
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$data = Get-Content -Raw -LiteralPath $InputJson | ConvertFrom-Json

foreach ($cue in $data.cues) {
  $id = [string]$cue.id
  if ($id -notmatch '^[A-Za-z0-9._-]+$') { throw "unsafe cue id: $id" }
  $path = Join-Path $OutputDir ($id + '.wav')
  $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
  try {
    $synth.SelectVoice($Voice)
    $synth.Rate = $Rate
    $synth.SetOutputToWaveFile($path)
    $synth.Speak([string]$cue.text)
  } finally {
    $synth.Dispose()
  }
}
