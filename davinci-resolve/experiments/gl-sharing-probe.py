#!/usr/bin/env python3
"""Test real GLX/EGL + OpenCL sharing; no Resolve or fake extensions."""
import argparse
import ctypes as c
import json
import os
from pathlib import Path


def bind(lib, name, args, result=c.c_int):
    fn = getattr(lib, name)
    fn.argtypes, fn.restype = args, result
    return fn


def graphics(backend):
    x = c.CDLL('libX11.so.6')
    gl = c.CDLL('libGL.so.1')
    display = bind(x, 'XOpenDisplay', [c.c_char_p], c.c_void_p)(None)
    if not display:
        raise RuntimeError('An X11 display is required; run with xvfb-run.')
    close = bind(x, 'XCloseDisplay', [c.c_void_p])
    if backend == 'glx':
        screen = bind(x, 'XDefaultScreen', [c.c_void_p])(display)
        attrs = (c.c_int * 7)(0x8010, 4, 0x8011, 1, 0x8012, 1, 0)
        count = c.c_int()
        configs = bind(gl, 'glXChooseFBConfig', [c.c_void_p, c.c_int, c.POINTER(c.c_int), c.POINTER(c.c_int)], c.POINTER(c.c_void_p))(display, screen, attrs, c.byref(count))
        if not count.value:
            close(display)
            raise RuntimeError('No GLX pbuffer configuration.')
        ctx = bind(gl, 'glXCreateNewContext', [c.c_void_p, c.c_void_p, c.c_int, c.c_void_p, c.c_int], c.c_void_p)(display, configs[0], 0x8014, None, 1)
        pb_attrs = (c.c_int * 5)(0x8041, 16, 0x8040, 16, 0)
        surface = bind(gl, 'glXCreatePbuffer', [c.c_void_p, c.c_void_p, c.POINTER(c.c_int)], c.c_ulong)(display, configs[0], pb_attrs)
        bind(x, 'XFree', [c.c_void_p])(configs)
        make_current = bind(gl, 'glXMakeContextCurrent', [c.c_void_p, c.c_ulong, c.c_ulong, c.c_void_p])
        if not ctx or not surface or not make_current(display, surface, surface, ctx):
            close(display)
            raise RuntimeError('Cannot create a current GLX context.')

        def cleanup():
            make_current(display, 0, 0, None)
            bind(gl, 'glXDestroyPbuffer', [c.c_void_p, c.c_ulong], None)(display, surface)
            bind(gl, 'glXDestroyContext', [c.c_void_p, c.c_void_p], None)(display, ctx)
            close(display)

        return gl, ctx, display, 0x200a, cleanup
    egl = c.CDLL('libEGL.so.1')
    ed = bind(egl, 'eglGetDisplay', [c.c_void_p], c.c_void_p)(display)
    major, minor = c.c_int(), c.c_int()
    if not bind(egl, 'eglInitialize', [c.c_void_p, c.POINTER(c.c_int), c.POINTER(c.c_int)])(ed, c.byref(major), c.byref(minor)):
        close(display)
        raise RuntimeError('EGL/X11 initialization failed.')
    bind(egl, 'eglBindAPI', [c.c_uint])(0x30a2)
    attrs = (c.c_int * 5)(0x3033, 1, 0x3040, 8, 0x3038)
    config, count = c.c_void_p(), c.c_int()
    bind(egl, 'eglChooseConfig', [c.c_void_p, c.POINTER(c.c_int), c.POINTER(c.c_void_p), c.c_int, c.POINTER(c.c_int)])(ed, attrs, c.byref(config), 1, c.byref(count))
    pb_attrs = (c.c_int * 5)(0x3057, 16, 0x3056, 16, 0x3038)
    ctx_attrs = (c.c_int * 1)(0x3038)
    surface = bind(egl, 'eglCreatePbufferSurface', [c.c_void_p, c.c_void_p, c.POINTER(c.c_int)], c.c_void_p)(ed, config, pb_attrs)
    ctx = bind(egl, 'eglCreateContext', [c.c_void_p, c.c_void_p, c.c_void_p, c.POINTER(c.c_int)], c.c_void_p)(ed, config, None, ctx_attrs)
    make_current = bind(egl, 'eglMakeCurrent', [c.c_void_p, c.c_void_p, c.c_void_p, c.c_void_p])
    if not count.value or not ctx or not surface or not make_current(ed, surface, surface, ctx):
        bind(egl, 'eglTerminate', [c.c_void_p])(ed)
        close(display)
        raise RuntimeError('Cannot create a current EGL/OpenGL context.')

    def cleanup():
        make_current(ed, None, None, None)
        bind(egl, 'eglDestroyContext', [c.c_void_p, c.c_void_p])(ed, ctx)
        bind(egl, 'eglDestroySurface', [c.c_void_p, c.c_void_p])(ed, surface)
        bind(egl, 'eglTerminate', [c.c_void_p])(ed)
        close(display)

    return gl, ctx, ed, 0x2009, cleanup


def shared_buffer(gl, cl, context, device):
    """Write a GL buffer through OpenCL and read it back through OpenGL."""
    result = {'passed': False}
    buf, err = c.c_uint(), c.c_int()
    bind(gl, 'glGenBuffers', [c.c_int, c.POINTER(c.c_uint)], None)(1, c.byref(buf))
    bind(gl, 'glBindBuffer', [c.c_uint, c.c_uint], None)(0x8892, buf.value)
    initial = (c.c_uint * 4)(7, 8, 9, 10)
    bind(gl, 'glBufferData', [c.c_uint, c.c_ssize_t, c.c_void_p, c.c_uint], None)(0x8892, 16, initial, 0x88e8)
    bind(gl, 'glFinish', [], None)()
    mem = queue = None
    try:
        mem = bind(cl, 'clCreateFromGLBuffer', [c.c_void_p, c.c_ulong, c.c_uint, c.POINTER(c.c_int)], c.c_void_p)(context, 1, buf.value, c.byref(err))
        result['createFromGLBufferError'] = err.value
        if not mem:
            return result
        queue = bind(cl, 'clCreateCommandQueue', [c.c_void_p, c.c_void_p, c.c_ulong, c.POINTER(c.c_int)], c.c_void_p)(context, device, 0, c.byref(err))
        result['queueError'] = err.value
        if not queue:
            return result
        objects = (c.c_void_p * 1)(mem)
        signature = [c.c_void_p, c.c_uint, c.POINTER(c.c_void_p), c.c_uint, c.c_void_p, c.c_void_p]
        result['acquireError'] = bind(cl, 'clEnqueueAcquireGLObjects', signature)(queue, 1, objects, 0, None, None)
        if result['acquireError']:
            return result
        updated = (c.c_uint * 4)(42, 8, 9, 10)
        result['writeError'] = bind(cl, 'clEnqueueWriteBuffer', [c.c_void_p, c.c_void_p, c.c_uint, c.c_size_t, c.c_size_t, c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p])(queue, mem, 1, 0, 16, updated, 0, None, None)
        result['releaseError'] = bind(cl, 'clEnqueueReleaseGLObjects', signature)(queue, 1, objects, 0, None, None)
        result['finishError'] = bind(cl, 'clFinish', [c.c_void_p])(queue)
        restored = (c.c_uint * 4)()
        bind(gl, 'glGetBufferSubData', [c.c_uint, c.c_ssize_t, c.c_ssize_t, c.c_void_p], None)(0x8892, 0, 16, restored)
        result['valuesReadByOpenGL'] = list(restored)
        result['passed'] = list(restored) == list(updated) and all(result[k] == 0 for k in ['acquireError', 'writeError', 'releaseError', 'finishError'])
        return result
    finally:
        if queue:
            bind(cl, 'clReleaseCommandQueue', [c.c_void_p])(queue)
        if mem:
            bind(cl, 'clReleaseMemObject', [c.c_void_p])(mem)
        bind(gl, 'glDeleteBuffers', [c.c_int, c.POINTER(c.c_uint)], None)(1, c.byref(buf))


def probe(backend):
    result = {'backend': backend, 'physicalGpuDeviceNodes': [str(p) for p in Path('/dev/dri').glob('renderD*')] + [str(p) for p in Path('/dev').glob('nvidia[0-9]*')], 'udmabufPresent': Path('/dev/udmabuf').exists(), 'deviceTypeOverride': os.environ.get('RUSTICL_DEVICE_TYPE'), 'devices': [], 'glSharingPassed': False, 'resolveTested': False}
    gl, ctx, display, display_key, cleanup = graphics(backend)
    try:
        get_string = bind(gl, 'glGetString', [c.c_uint], c.c_char_p)
        result['glRenderer'] = get_string(0x1f01).decode()
        result['glVersion'] = get_string(0x1f02).decode()
        cl = c.CDLL('libOpenCL.so.1')
        ids = bind(cl, 'clGetPlatformIDs', [c.c_uint, c.POINTER(c.c_void_p), c.POINTER(c.c_uint)])
        count = c.c_uint()
        if ids(0, None, c.byref(count)) or not count.value:
            result['error'] = 'No OpenCL platform.'
            return result
        platforms = (c.c_void_p * count.value)()
        ids(count, platforms, None)
        device_ids = bind(cl, 'clGetDeviceIDs', [c.c_void_p, c.c_ulong, c.c_uint, c.POINTER(c.c_void_p), c.POINTER(c.c_uint)])
        info = bind(cl, 'clGetDeviceInfo', [c.c_void_p, c.c_uint, c.c_size_t, c.c_void_p, c.POINTER(c.c_size_t)])
        create = bind(cl, 'clCreateContext', [c.POINTER(c.c_ssize_t), c.c_uint, c.POINTER(c.c_void_p), c.c_void_p, c.c_void_p, c.POINTER(c.c_int)], c.c_void_p)
        for platform in platforms:
            n = c.c_uint()
            if device_ids(platform, 0xffffffff, 0, None, c.byref(n)):
                continue
            devices = (c.c_void_p * n.value)()
            device_ids(platform, 0xffffffff, n, devices, None)
            for device in devices:
                def device_string(key):
                    size = c.c_size_t()
                    if info(device, key, 0, None, c.byref(size)):
                        return ''
                    value = c.create_string_buffer(size.value)
                    info(device, key, size, value, None)
                    return value.value.decode()

                extensions = device_string(0x1030).split()
                item = {'name': device_string(0x102b), 'glSharingAdvertised': 'cl_khr_gl_sharing' in extensions, 'extensions': extensions}
                device_type, image_support = c.c_ulong(), c.c_uint()
                info(device, 0x1000, c.sizeof(device_type), c.byref(device_type), None)
                info(device, 0x1016, c.sizeof(image_support), c.byref(image_support), None)
                item.update(reportedDeviceType=device_type.value, imageSupport=bool(image_support.value))
                err, dev = c.c_int(), c.c_void_p(device)
                basic_props = (c.c_ssize_t * 3)(0x1084, platform, 0)
                basic = create(basic_props, 1, c.byref(dev), None, None, c.byref(err))
                item['basicContextError'] = err.value
                if basic:
                    bind(cl, 'clReleaseContext', [c.c_void_p])(basic)
                props = (c.c_ssize_t * 7)(0x1084, platform, 0x2008, ctx, display_key, display, 0)
                shared = create(props, 1, c.byref(dev), None, None, c.byref(err))
                item['glSharedContextError'], item['glSharedContextCreated'] = err.value, bool(shared)
                if shared:
                    try:
                        item['sharedBufferRoundTrip'] = shared_buffer(gl, cl, shared, device)
                    finally:
                        bind(cl, 'clReleaseContext', [c.c_void_p])(shared)
                    result['glSharingPassed'] |= item['sharedBufferRoundTrip']['passed']
                result['devices'].append(item)
        return result
    finally:
        cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=['glx', 'egl'], default='glx')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = probe(args.backend)
    except Exception as exc:
        result = {'backend': args.backend, 'glSharingPassed': False, 'resolveTested': False, 'error': f'{type(exc).__name__}: {exc}'}
    encoded = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + '\n')
    print(encoded)


if __name__ == '__main__':
    main()
