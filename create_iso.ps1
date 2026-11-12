$sourcePath = "D:\BurgoodAccsesCantrol\dist\BurgoodAccessControl"
$isoPath = "D:\BurgoodAccsesCantrol\BurgoodAccessControl.iso"

Write-Output "ISO yaratilmoqda: $isoPath"

if (Test-Path $isoPath) {
    Remove-Item $isoPath -Force
}

$fsi = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
$fsi.ChooseImageDefaultsForMediaType(12)
$fsi.FileSystemsToCreate = 3 # ISO9660 + Joliet (Windows uchun eng mos)
$fsi.VolumeName = "BURGOOD_AC"
$root = $fsi.Root
$root.AddTree($sourcePath, $false)

$resultImage = $fsi.CreateResultImage()
$stream = $resultImage.ImageStream

$fileStream = [System.IO.File]::Open($isoPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
$buffer = New-Object byte[] (1024 * 1024 * 2) # 2MB buffer

$iStream = [System.Runtime.InteropServices.ComTypes.IStream]$stream
$bytesRead = [IntPtr]::Zero
$readBuffer = New-Object byte[] (1024 * 1024 * 2)

$comStream = $stream
$totalWritten = 0

# Streamni faylga o'qib yozish
$buf = New-Object byte[] 65536
while ($true) {
    [int]$bytesRead = 0
    try {
        $bytesRead = $comStream.Read($buf, 0, $buf.Length)
    } catch {
        break
    }
    if ($bytesRead -le 0) { break }
    $fileStream.Write($buf, 0, $bytesRead)
    $totalWritten += $bytesRead
}

$fileStream.Close()
Write-Output "ISO muvaffaqiyatli yaratildi! Hajmi: $([math]::Round($totalWritten / 1MB, 2)) MB"
