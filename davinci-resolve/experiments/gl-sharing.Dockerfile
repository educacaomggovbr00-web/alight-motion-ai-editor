# For the isolated GitHub Actions runner; Debian's signed repositories only.
ARG DEBIAN_IMAGE=debian:13-slim
FROM ${DEBIAN_IMAGE}
ARG MESA_BACKPORTS=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && if [ "$MESA_BACKPORTS" = 1 ]; then printf '%s\n' 'deb https://deb.debian.org/debian trixie-backports main' > /etc/apt/sources.list.d/mesa-backports.list; fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 xvfb xauth clinfo mesa-utils vulkan-tools libgl1 libegl1 libx11-6 \
    && if [ "$MESA_BACKPORTS" = 1 ]; then apt-get install -y -t trixie-backports mesa-opencl-icd mesa-vulkan-drivers libgl1-mesa-dri libglx-mesa0 libegl-mesa0 libgbm1; else apt-get install -y mesa-opencl-icd mesa-vulkan-drivers libgl1-mesa-dri libglx-mesa0 libegl-mesa0 libgbm1; fi \
    && rm -rf /var/lib/apt/lists/*
ENV LIBGL_ALWAYS_SOFTWARE=1 RUSTICL_ENABLE=llvmpipe,zink GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink LP_NUM_THREADS=2 VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.json
WORKDIR /experiment
COPY gl-sharing-probe.py /experiment/gl-sharing-probe.py
COPY vulkan-dmabuf-probe.py /experiment/vulkan-dmabuf-probe.py
