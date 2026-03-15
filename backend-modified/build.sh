#!/usr/bin/env bash
# exit on error
set -o errexit

# ── Install OpenJDK 21 (portable, no root required) ────────────────────────
JDK_VERSION="21.0.3"
JDK_DIR="$HOME/.jdk/jdk-${JDK_VERSION}"
JDK_TARBALL="$HOME/.jdk/openjdk-${JDK_VERSION}.tar.gz"
JDK_URL="https://github.com/adoptium/temurin21-binaries/releases/download/jdk-${JDK_VERSION}%2B9/OpenJDK21U-jdk_x64_linux_hotspot_${JDK_VERSION}_9.tar.gz"

if [ ! -d "$JDK_DIR" ]; then
    echo "Downloading OpenJDK ${JDK_VERSION}..."
    mkdir -p "$HOME/.jdk"
    curl -L "$JDK_URL" -o "$JDK_TARBALL"
    tar -xzf "$JDK_TARBALL" -C "$HOME/.jdk"
    # The extracted folder name includes the build suffix; rename for consistency
    EXTRACTED=$(ls "$HOME/.jdk" | grep "jdk-${JDK_VERSION}" | head -1)
    mv "$HOME/.jdk/$EXTRACTED" "$JDK_DIR" 2>/dev/null || true
    rm -f "$JDK_TARBALL"
    echo "OpenJDK ${JDK_VERSION} installed at $JDK_DIR"
else
    echo "OpenJDK ${JDK_VERSION} already present, skipping download."
fi

export JAVA_HOME="$JDK_DIR"
export PATH="$JAVA_HOME/bin:$PATH"

# Persist JAVA_HOME and PATH for the Render runtime (gunicorn process)
echo "export JAVA_HOME=\"$JDK_DIR\""   >> "$HOME/.profile"
echo "export PATH=\"$JAVA_HOME/bin:\$PATH\"" >> "$HOME/.profile"

java -version
javac -version

# ── Python dependencies & Django setup ─────────────────────────────────────
pip install -r requirements.txt

python manage.py collectstatic --no-input