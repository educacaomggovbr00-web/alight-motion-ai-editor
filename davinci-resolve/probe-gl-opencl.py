import ctypes as c,json
x=c.CDLL('libX11.so.6');gl=c.CDLL('libGL.so.1');cl=c.CDLL('libOpenCL.so.1')
x.XOpenDisplay.argtypes=[c.c_char_p];x.XOpenDisplay.restype=c.c_void_p
x.XDefaultScreen.argtypes=[c.c_void_p];x.XDefaultScreen.restype=c.c_int
x.XCloseDisplay.argtypes=[c.c_void_p]
gl.glXChooseFBConfig.argtypes=[c.c_void_p,c.c_int,c.POINTER(c.c_int),c.POINTER(c.c_int)];gl.glXChooseFBConfig.restype=c.POINTER(c.c_void_p)
gl.glXCreateNewContext.argtypes=[c.c_void_p,c.c_void_p,c.c_int,c.c_void_p,c.c_int];gl.glXCreateNewContext.restype=c.c_void_p
gl.glXCreatePbuffer.argtypes=[c.c_void_p,c.c_void_p,c.POINTER(c.c_int)];gl.glXCreatePbuffer.restype=c.c_ulong
gl.glXMakeContextCurrent.argtypes=[c.c_void_p,c.c_ulong,c.c_ulong,c.c_void_p];gl.glXMakeContextCurrent.restype=c.c_int
gl.glGetString.argtypes=[c.c_uint];gl.glGetString.restype=c.c_char_p
cl.clGetPlatformIDs.argtypes=[c.c_uint,c.POINTER(c.c_void_p),c.POINTER(c.c_uint)]
cl.clGetDeviceIDs.argtypes=[c.c_void_p,c.c_ulong,c.c_uint,c.POINTER(c.c_void_p),c.POINTER(c.c_uint)]
cl.clCreateContext.argtypes=[c.POINTER(c.c_ssize_t),c.c_uint,c.POINTER(c.c_void_p),c.c_void_p,c.c_void_p,c.POINTER(c.c_int)];cl.clCreateContext.restype=c.c_void_p
cl.clReleaseContext.argtypes=[c.c_void_p]
d=x.XOpenDisplay(None)
if not d:raise RuntimeError('X display unavailable')
attrs=(c.c_int*7)(0x8010,4,0x8011,1,0x8012,1,0);n=c.c_int()
f=gl.glXChooseFBConfig(d,x.XDefaultScreen(d),attrs,c.byref(n))
if not n.value:raise RuntimeError('No GLX framebuffer configuration')
ctx=gl.glXCreateNewContext(d,f[0],0x8014,None,1)
pattr=(c.c_int*5)(0x8041,16,0x8040,16,0)
pbuf=gl.glXCreatePbuffer(d,f[0],pattr)
if not ctx or not gl.glXMakeContextCurrent(d,pbuf,pbuf,ctx):raise RuntimeError('GLX context failed')
plat=c.c_void_p();dev=c.c_void_p()
assert cl.clGetPlatformIDs(1,c.byref(plat),None)==0
assert cl.clGetDeviceIDs(plat,4,1,c.byref(dev),None)==0
err=c.c_int()
basic=(c.c_ssize_t*3)(0x1084,plat.value,0)
a=cl.clCreateContext(basic,1,c.byref(dev),None,None,c.byref(err));basic_error=err.value
if a:cl.clReleaseContext(a)
shared=(c.c_ssize_t*7)(0x1084,plat.value,0x2008,ctx,0x200a,d,0)
b=cl.clCreateContext(shared,1,c.byref(dev),None,None,c.byref(err));share_error=err.value
if b:cl.clReleaseContext(b)
print(json.dumps({'glRenderer':gl.glGetString(0x1f01).decode(),'basicContextError':basic_error,'glSharedContextError':share_error,'glSharingPassed':bool(b),'physicalGpu':False}))
