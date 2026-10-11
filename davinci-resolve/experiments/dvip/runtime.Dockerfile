# Same driver image used for the gate and the original application.
FROM codex-mesa-dvip
RUN apt-get update && apt-get install -y --no-install-recommends \
 ffmpeg imagemagick tesseract-ocr xdotool x11-utils libglib2.0-0t64 \
 libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 libglu1-mesa \
 libapr1t64 libaprutil1t64 libasound2t64 libnss3 libxss1 libxrandr2 \
 libxtst6 libxi6 libxinerama1 libxrender1 libcurl4t64 libcrypt1 \
 libfontconfig1 libfreetype6 libpulse0 libxcb-composite0 libxcb-render-util0 \
 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-shape0 libxcb-xfixes0 libxcb-sync1 \
 && rm -rf /var/lib/apt/lists/*
COPY dvip/source.py dvip/supervise.py dvip/edit_smoke.py /experiment/dvip/
RUN dpkg-query -W > /experiment/runtime-package-versions.txt \
 && find /opt/mesa-experimental/lib -maxdepth 1 -type f -exec sha256sum {} + > /experiment/mesa-library-hashes.txt
