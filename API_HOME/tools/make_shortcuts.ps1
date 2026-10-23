param([string]$Pyw,[string]$AppHome)
# Creates ONE_MENU shortcuts on the Desktop and in the Start Menu.
$shell=New-Object -ComObject WScript.Shell
foreach($dir in @([Environment]::GetFolderPath("Desktop"),[Environment]::GetFolderPath("Programs"))){
  $s=$shell.CreateShortcut((Join-Path $dir "ONE_MENU.lnk"))
  $s.TargetPath=$Pyw
  $s.Arguments='"'+(Join-Path $AppHome "engine\web.py")+'"'
  $s.WorkingDirectory=$AppHome
  $s.IconLocation=(Join-Path $AppHome "web\ONE_MENU.ico")
  $s.Description="ONE_MENU - every API pipeline"
  $s.Save()
}
