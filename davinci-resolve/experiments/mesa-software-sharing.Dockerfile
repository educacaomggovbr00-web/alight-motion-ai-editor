FROM debian:sid-slim
RUN sed -i 's/Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl python3 meson ninja-build xvfb xauth clinfo mesa-utils vulkan-tools libgl1 libegl1 libx11-6 \
 && apt-get build-dep -y --no-install-recommends mesa \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN curl --fail --location --retry 2 https://deb.debian.org/debian/pool/main/m/mesa/mesa_26.2.4.orig.tar.xz -o mesa.tar.xz \
 && tar -xJf mesa.tar.xz && rm mesa.tar.xz
COPY patch-mesa-software-sharing.py /build/patch.py
RUN python3 /build/patch.py /build/mesa-26.2.4 > /build/patch-result.json \
 && meson setup /build/compiled /build/mesa-26.2.4 --prefix=/opt/mesa-experimental --libdir=lib --buildtype=release \
 -Dgallium-drivers=zink,llvmpipe -Dvulkan-drivers=swrast -Dgallium-rusticl=true \
 -Dplatforms=x11 -Dglx=dri -Degl=enabled -Dllvm=enabled -Dshared-llvm=enabled \
 -Dgallium-va=disabled -Dvideo-codecs=[] -Dbuild-tests=false -Dtools=[] \
 && ninja -C /build/compiled -j 2 && meson install -C /build/compiled
ENV LD_LIBRARY_PATH=/opt/mesa-experimental/lib LIBGL_DRIVERS_PATH=/opt/mesa-experimental/lib/dri OCL_ICD_VENDORS=/opt/mesa-experimental/etc/OpenCL/vendors VK_DRIVER_FILES=/opt/mesa-experimental/share/vulkan/icd.d/lvp_icd.json
ENV LIBGL_ALWAYS_SOFTWARE=1 RUSTICL_ENABLE=zink GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink LP_NUM_THREADS=2
WORKDIR /experiment
COPY gl-sharing-probe.py vulkan-dmabuf-probe.py run-gl-sharing-matrix.py /experiment/
