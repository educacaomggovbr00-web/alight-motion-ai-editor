param([switch]$RequireWindows11, [string]$Output = 'premiere-cloud/runtime/warp.json')
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$isWindows11 = $os.ProductType -eq 1 -and [int]$os.BuildNumber -ge 22000
if ($RequireWindows11 -and -not $isWindows11) { throw 'Este teste exige Windows 11 desktop' }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PremiereWarpProbe {
    [DllImport("d3d11.dll", CallingConvention=CallingConvention.StdCall)]
    static extern int D3D11CreateDevice(IntPtr adapter, uint driverType,
        IntPtr software, uint flags, uint[] levels, uint count, uint sdk,
        out IntPtr device, out uint level, out IntPtr context);
    public static uint Test() {
        IntPtr device=IntPtr.Zero, context=IntPtr.Zero; uint level;
        try {
            // D3D_DRIVER_TYPE_WARP = 5; SDK version = 7.
            int hr = D3D11CreateDevice(IntPtr.Zero, 5, IntPtr.Zero, 0,
                new uint[]{0xb000}, 1, 7, out device, out level, out context);
            if(hr < 0) Marshal.ThrowExceptionForHR(hr);
            if(device == IntPtr.Zero || context == IntPtr.Zero || level < 0xb000)
                throw new InvalidOperationException("WARP device unavailable");
            return level;
        } finally {
            if(context != IntPtr.Zero) Marshal.Release(context);
            if(device != IntPtr.Zero) Marshal.Release(device);
        }
    }
}
'@
$level = [PremiereWarpProbe]::Test()
$parent = Split-Path -Parent $Output
if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
@{state='testado'; scope='criacao_dispositivo_Direct3D11_WARP_apenas';
  windows11=$isWindows11; osCaption=$os.Caption; build=$os.BuildNumber;
  featureLevel=('0x{0:x}' -f $level); renderer='WARP_CPU';
  gpuPhysicalProven=$false; premiereStarted=$false; exportProven=$false
} | ConvertTo-Json | Set-Content -LiteralPath $Output -Encoding utf8
Write-Host 'Dispositivo WARP Direct3D11 criado. Nao testa renderizacao nem Premiere.'
