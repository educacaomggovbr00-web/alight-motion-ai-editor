/*
 * Diagnóstico aberto para o ambiente Windows simulado pelo Wine.
 * Compila com MinGW-w64; não usa nem distribui código da Adobe.
 * Verifica API D3D11 e enumera adaptadores DXGI, sem fazer benchmark.
 */
#define COBJMACROS
#include <initguid.h>
#include <windows.h>
#include <stdio.h>
#include <d3d11.h>
#include <dxgi1_2.h>

static void adapters(void) {
    IDXGIFactory1 *factory = NULL;
    HRESULT hr = CreateDXGIFactory1(&IID_IDXGIFactory1, (void **)&factory);
    printf("DXGI.Factory.HRESULT=0x%08lx\n", (unsigned long)hr);
    if (FAILED(hr) || !factory) return;
    for (UINT i = 0; i < 10; i++) {
        IDXGIAdapter1 *adapter = NULL;
        hr = IDXGIFactory1_EnumAdapters1(factory, i, &adapter);
        if (hr == DXGI_ERROR_NOT_FOUND) break;
        if (FAILED(hr) || !adapter) break;
        DXGI_ADAPTER_DESC1 d;
        hr = IDXGIAdapter1_GetDesc1(adapter, &d);
        if (SUCCEEDED(hr)) {
            char name[256] = {0};
            WideCharToMultiByte(CP_UTF8, 0, d.Description, -1, name, sizeof(name), NULL, NULL);
            printf("DXGI.Adapter.%u.Name=%s\n", i, name);
            printf("DXGI.Adapter.%u.VRAM_MiB=%llu\n", i,
                   (unsigned long long)(d.DedicatedVideoMemory / (1024 * 1024)));
            printf("DXGI.Adapter.%u.SoftwareFlag=%s\n", i,
                   (d.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) ? "yes" : "no");
        }
        IDXGIAdapter1_Release(adapter);
    }
    IDXGIFactory1_Release(factory);
}

int main(void) {
    ID3D11Device *device = NULL;
    ID3D11DeviceContext *context = NULL;
    D3D_FEATURE_LEVEL level = 0;
    printf("D3D11.Test=Wine on GitHub Actions; not Adobe Premiere\n");
    fflush(stdout);
    adapters();
    HRESULT hr = D3D11CreateDevice(
        NULL, D3D_DRIVER_TYPE_HARDWARE, NULL, 0,
        NULL, 0, D3D11_SDK_VERSION, &device, &level, &context
    );
    printf("D3D11.CreateDevice.HRESULT=0x%08lx\n", (unsigned long)hr);
    if (SUCCEEDED(hr)) {
        printf("D3D11.FeatureLevel=0x%04x\n", (unsigned int)level);
        if (context) ID3D11DeviceContext_Release(context);
        if (device) ID3D11Device_Release(device);
        return 0;
    }
    return 2;
}
