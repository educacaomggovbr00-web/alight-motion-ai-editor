import ctypes as c
import json
import sys
from pathlib import Path

cl = c.CDLL('libOpenCL.so.1')
cl.clGetPlatformIDs.argtypes = [c.c_uint, c.POINTER(c.c_void_p), c.POINTER(c.c_uint)]
cl.clGetDeviceIDs.argtypes = [c.c_void_p, c.c_ulong, c.c_uint, c.POINTER(c.c_void_p), c.POINTER(c.c_uint)]
cl.clCreateContext.argtypes = [c.POINTER(c.c_ssize_t), c.c_uint, c.POINTER(c.c_void_p), c.c_void_p, c.c_void_p, c.POINTER(c.c_int)]
cl.clCreateContext.restype = c.c_void_p
cl.clCreateCommandQueue.argtypes = [c.c_void_p, c.c_void_p, c.c_ulong, c.POINTER(c.c_int)]
cl.clCreateCommandQueue.restype = c.c_void_p
cl.clCreateBuffer.argtypes = [c.c_void_p, c.c_ulong, c.c_size_t, c.c_void_p, c.POINTER(c.c_int)]
cl.clCreateBuffer.restype = c.c_void_p
cl.clEnqueueFillBuffer.argtypes = [c.c_void_p, c.c_void_p, c.c_void_p, c.c_size_t, c.c_size_t, c.c_size_t, c.c_uint, c.c_void_p, c.c_void_p]
cl.clEnqueueReadBuffer.argtypes = [c.c_void_p, c.c_void_p, c.c_uint, c.c_size_t, c.c_size_t, c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p]
cl.clFinish.argtypes = [c.c_void_p]
for name in ['clReleaseMemObject', 'clReleaseCommandQueue', 'clReleaseContext']:
    getattr(cl, name).argtypes = [c.c_void_p]

def check(code):
    if code != 0:
        raise RuntimeError(f'OpenCL error {code}')

platform, device, error = c.c_void_p(), c.c_void_p(), c.c_int()
check(cl.clGetPlatformIDs(1, c.byref(platform), None))
check(cl.clGetDeviceIDs(platform, 0xFFFFFFFF, 1, c.byref(device), None))
props = (c.c_ssize_t * 3)(0x1084, platform.value, 0)
context = cl.clCreateContext(props, 1, c.byref(device), None, None, c.byref(error))
check(error.value)
queue, buffer = None, None
try:
    queue = cl.clCreateCommandQueue(context, device, 0, c.byref(error))
    check(error.value)
    size = 64 * 1024 * 1024
    buffer = cl.clCreateBuffer(context, 1, size, None, c.byref(error))
    check(error.value)
    pattern = c.c_uint32(0x12345678)
    check(cl.clEnqueueFillBuffer(queue, buffer, c.byref(pattern), 4, 0, size, 0, None, None))
    check(cl.clFinish(queue))
    observed = []
    for offset in [0, size - 4]:
        value = c.c_uint32()
        check(cl.clEnqueueReadBuffer(queue, buffer, 1, offset, 4, c.byref(value), 0, None, None))
        observed.append(value.value)
    if observed != [pattern.value, pattern.value]:
        raise RuntimeError('Buffer verification failed')
    Path(sys.argv[1]).write_text(json.dumps({'bufferBytes': size, 'filledAndRead': True, 'values': observed, 'physicalGpu': False}))
    sys.stdin.read(1)
finally:
    if buffer:
        cl.clReleaseMemObject(buffer)
    if queue:
        cl.clReleaseCommandQueue(queue)
    cl.clReleaseContext(context)
