# For the isolated GitHub Actions runner; Debian's signed repositories only.
FROM debian:13-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && printf '%s\n' 'deb https://deb.debian.org/debian trixie-backports main' > /etc/apt/sources.list.d/mesa-backports.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 xvfb xauth clinfo mesa-utils vulkan-tools libgl1 libegl1 libx11-6 libclc-19 libclang-common-19-dev \
    && apt-get install -y --no-install-recommends -t trixie-backports mesa-opencl-icd mesa-vulkan-drivers libgl1-mesa-dri libglx-mesa0 libegl-mesa0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*
ENV LIBGL_ALWAYS_SOFTWARE=1 RUSTICL_ENABLE=llvmpipe,zink GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink LP_NUM_THREADS=2
WORKDIR /experiment
COPY gl-sharing-probe.py /experiment/gl-sharing-probe.py
