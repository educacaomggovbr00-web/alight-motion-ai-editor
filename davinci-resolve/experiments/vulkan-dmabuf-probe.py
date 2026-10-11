#!/usr/bin/env python3
"""Allocate, export, import and verify a real 4 KiB Vulkan DMA-BUF."""
import argparse
import ctypes as c
import json
import os
import struct
from pathlib import Path


def structure(name, fields):
    return type(name, (c.Structure,), {'_fields_': fields})


U, P, H, Z = c.c_uint32, c.c_void_p, c.c_uint64, c.c_size_t
header = [('sType', U), ('pNext', P)]
App = structure('App', header + [('name', c.c_char_p), ('version', U), ('engine', c.c_char_p), ('engineVersion', U), ('apiVersion', U)])
Instance = structure('Instance', header + [('flags', U), ('app', c.POINTER(App)), ('layers', U), ('layerNames', P), ('extensions', U), ('extensionNames', P)])
ExternalInfo = structure('ExternalInfo', header + [('flags', U), ('usage', U), ('handleType', U)])
ExternalProps = structure('ExternalProps', header + [('features', U), ('exportFromImportedTypes', U), ('compatibleTypes', U)])
Extension = structure('Extension', [('name', c.c_char * 256), ('version', U)])
QueueInfo = structure('QueueInfo', header + [('flags', U), ('family', U), ('count', U), ('priorities', c.POINTER(c.c_float))])
DeviceInfo = structure('DeviceInfo', header + [('flags', U), ('queueCount', U), ('queueInfos', c.POINTER(QueueInfo)), ('layers', U), ('layerNames', P), ('extensions', U), ('extensionNames', P), ('features', P)])
ExternalBuffer = structure('ExternalBuffer', header + [('handleTypes', U)])
Buffer = structure('Buffer', header + [('flags', U), ('size', H), ('usage', U), ('sharingMode', U), ('familyCount', U), ('families', P)])
Requirements = structure('Requirements', [('size', H), ('alignment', H), ('typeBits', U)])
MemoryType = structure('MemoryType', [('flags', U), ('heap', U)])
MemoryHeap = structure('MemoryHeap', [('size', H), ('flags', U)])
MemoryProperties = structure('MemoryProperties', [('count', U), ('types', MemoryType * 32), ('heapCount', U), ('heaps', MemoryHeap * 16)])
Dedicated = structure('Dedicated', header + [('image', H), ('buffer', H)])
ExportMemory = structure('ExportMemory', header + [('handleTypes', U)])
ImportMemory = structure('ImportMemory', header + [('handleType', U), ('fd', c.c_int)])
Allocation = structure('Allocation', header + [('size', H), ('type', U)])
GetFd = structure('GetFd', header + [('memory', H), ('handleType', U)])


def ptr(value):
    return c.cast(c.pointer(value), P)


def probe(engine):
    vk = c.CDLL('libvulkan.so.1')

    def fn(name, args, returns=c.c_int):
        f = getattr(vk, name)
        f.argtypes, f.restype = args, returns
        return f

    def check(code, operation):
        if code != 0:
            raise RuntimeError(f'{operation}: VkResult {code}')

    app = App(0, None, b'codex-dmabuf-probe', 1, engine.encode(), 1, (1 << 22) | (1 << 12))
    create_info = Instance(1, None, 0, c.pointer(app), 0, None, 0, None)
    instance, device = P(), P()
    buffers, memories, mapped = [], [], []
    fd = None
    result = {'engine': engine, 'udmabufPresent': Path('/dev/udmabuf').exists(), 'vulkanDmaBufRoundTripPassed': False, 'resolveTested': False}
    try:
        check(fn('vkCreateInstance', [P, P, c.POINTER(P)])(c.byref(create_info), None, c.byref(instance)), 'create instance')
        count = U()
        enumerate_devices = fn('vkEnumeratePhysicalDevices', [P, c.POINTER(U), c.POINTER(P)])
        check(enumerate_devices(instance, c.byref(count), None), 'enumerate physical devices')
        if count.value != 1:
            raise RuntimeError(f'Expected the isolated Lavapipe ICD, got {count.value} devices.')
        physicals = (P * count.value)()
        check(enumerate_devices(instance, c.byref(count), physicals), 'enumerate device')
        physical = physicals[0]
        props_raw = c.create_string_buffer(4096)
        fn('vkGetPhysicalDeviceProperties', [P, P], None)(physical, props_raw)
        result['deviceName'] = props_raw.raw[20:276].split(b'\0')[0].decode()
        result['vulkanDeviceType'] = struct.unpack_from('=I', props_raw.raw, 16)[0]
        ext_count = U()
        ext_fn = fn('vkEnumerateDeviceExtensionProperties', [P, c.c_char_p, c.POINTER(U), c.POINTER(Extension)])
        check(ext_fn(physical, None, c.byref(ext_count), None), 'enumerate extensions')
        ext_data = (Extension * ext_count.value)()
        check(ext_fn(physical, None, c.byref(ext_count), ext_data), 'read extensions')
        extensions = [x.name.decode() for x in ext_data]
        result['dmaBufExtensionAdvertised'] = 'VK_EXT_external_memory_dma_buf' in extensions
        result['externalSemaphoreFdAdvertised'] = 'VK_KHR_external_semaphore_fd' in extensions
        if not result['dmaBufExtensionAdvertised']:
            result['blockedReason'] = 'Vulkan did not advertise DMA-BUF to this engine.'
            return result
        external_info = ExternalInfo(1000071002, None, 0, 3, 0x200)
        external_props = ExternalProps(1000071003, None)
        fn('vkGetPhysicalDeviceExternalBufferProperties', [P, P, P], None)(physical, c.byref(external_info), c.byref(external_props))
        result.update(externalMemoryFeatures=external_props.features, importOffered=bool(external_props.features & 4), exportOffered=bool(external_props.features & 2))
        if (external_props.features & 6) != 6:
            result['blockedReason'] = 'DMA-BUF import and export are not both offered.'
            return result
        priorities = (c.c_float * 1)(1.0)
        queue = QueueInfo(2, None, 0, 0, 1, priorities)
        names = (c.c_char_p * 2)(b'VK_KHR_external_memory_fd', b'VK_EXT_external_memory_dma_buf')
        device_info = DeviceInfo(3, None, 0, 1, c.pointer(queue), 0, None, 2, c.cast(names, P), None)
        check(fn('vkCreateDevice', [P, P, P, c.POINTER(P)])(physical, c.byref(device_info), None, c.byref(device)), 'create device')
        mem_props = MemoryProperties()
        fn('vkGetPhysicalDeviceMemoryProperties', [P, P], None)(physical, c.byref(mem_props))
        for index in range(2):
            external_buffer = ExternalBuffer(1000072000, None, 0x200)
            buffer_info = Buffer(12, ptr(external_buffer), 0, 4096, 3, 0, 0, None)
            buffer = H()
            check(fn('vkCreateBuffer', [P, P, P, c.POINTER(H)])(device, c.byref(buffer_info), None, c.byref(buffer)), 'create buffer')
            buffers.append(buffer)
            requirement = Requirements()
            fn('vkGetBufferMemoryRequirements', [P, H, P], None)(device, buffer, c.byref(requirement))
            choices = [i for i in range(mem_props.count) if requirement.typeBits & (1 << i) and (mem_props.types[i].flags & 6) == 6]
            if not choices:
                raise RuntimeError('No host-visible coherent memory type for the test.')
            dedicated = Dedicated(1000127001, None, 0, buffer.value)
            external_memory = ExportMemory(1000072002, ptr(dedicated), 0x200) if index == 0 else ImportMemory(1000074000, ptr(dedicated), 0x200, fd)
            allocation = Allocation(5, ptr(external_memory), requirement.size, choices[0])
            memory = H()
            check(fn('vkAllocateMemory', [P, P, P, c.POINTER(H)])(device, c.byref(allocation), None, c.byref(memory)), 'allocate/export or import memory')
            memories.append(memory)
            if index == 1:
                fd = None  # Vulkan takes ownership only after a successful import.
            check(fn('vkBindBufferMemory', [P, H, H, H])(device, buffer, memory, 0), 'bind buffer memory')
            address = P()
            check(fn('vkMapMemory', [P, H, H, H, U, c.POINTER(P)])(device, memory, 0, 4096, 0, c.byref(address)), 'map memory')
            mapped.append(memory)
            if index == 0:
                original_address = address.value
                c.memmove(address, b'DMA-BUF-ORIGINAL!', 17)
                get_address = fn('vkGetDeviceProcAddr', [P, c.c_char_p], P)(device, b'vkGetMemoryFdKHR')
                if not get_address:
                    raise RuntimeError('vkGetMemoryFdKHR unavailable.')
                get_fd = c.CFUNCTYPE(c.c_int, P, P, c.POINTER(c.c_int))(get_address)
                fd_info, exported = GetFd(1000074002, None, memory.value, 0x200), c.c_int(-1)
                check(get_fd(device, c.byref(fd_info), c.byref(exported)), 'export DMA-BUF fd')
                fd = exported.value
                result['exportedFdValid'] = fd >= 0
            else:
                result['importReadOriginal'] = c.string_at(address, 17) == b'DMA-BUF-ORIGINAL!'
                c.memmove(address, b'DMA-BUF-MODIFIED!', 17)
                result['originalReadImportedWrite'] = c.string_at(original_address, 17) == b'DMA-BUF-MODIFIED!'
        result['vulkanDmaBufRoundTripPassed'] = result['importReadOriginal'] and result['originalReadImportedWrite']
        return result
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        return result
    finally:
        if fd is not None and fd >= 0:
            os.close(fd)
        if device.value:
            for memory in mapped:
                fn('vkUnmapMemory', [P, H], None)(device, memory)
            for buffer in buffers:
                fn('vkDestroyBuffer', [P, H, P], None)(device, buffer, None)
            for memory in memories:
                fn('vkFreeMemory', [P, H, P], None)(device, memory, None)
            fn('vkDestroyDevice', [P, P], None)(device, None)
        if instance.value:
            fn('vkDestroyInstance', [P, P], None)(instance, None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', default='mesa zink')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = probe(args.engine)
    encoded = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + '\n')
    print(encoded)


if __name__ == '__main__':
    main()
