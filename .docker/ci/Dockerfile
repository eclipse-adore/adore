# .docker/ci/Dockerfile
FROM adore_base:latest

# -------------------------------------------------------------------
# CI-specific system dependencies (docs, test tooling, etc.)
# -------------------------------------------------------------------
COPY .docker/ci/apt.ci.txt /tmp/apt.ci.txt
RUN if [ -s /tmp/apt.ci.txt ]; then \
      apt-get update && \
      xargs -r -a /tmp/apt.ci.txt apt-get install -y && \
      rm -rf /var/lib/apt/lists/* /tmp/*; \
    else \
      echo "No CI APT dependencies listed in /tmp/apt.ci.txt"; \
    fi

# -------------------------------------------------------------------
# CI-specific Python dependencies (MkDocs Material, plugins, ...)
# -------------------------------------------------------------------
COPY .docker/ci/pip.ci.txt /tmp/pip.ci.txt
RUN if [ -s /tmp/pip.ci.txt ]; then \
      pip3 install --no-cache-dir --break-system-packages --ignore-installed -r /tmp/pip.ci.txt && \
      rm -f /tmp/pip.ci.txt; \
    else \
      echo "No CI pip dependencies listed in /tmp/pip.ci.txt"; \
    fi


# CI user (still UID/GID mapped so volume permissions behave)
ARG USERNAME=ci
ARG USER_UID=2001
ARG USER_GID=2001

RUN set -eux; \
    existing_user="$(getent passwd "${USER_UID}" | cut -d: -f1 || true)"; \
    if [ -n "${existing_user}" ]; then \
        echo "Renaming user ${existing_user} to ${USERNAME}"; \
        usermod -l "${USERNAME}" "${existing_user}"; \
        usermod -d "/home/${USERNAME}" -m "${USERNAME}"; \
        groupmod -n "${USERNAME}" "${existing_user}"; \
    else \
        echo "Creating new user ${USERNAME}"; \
        groupadd -g "${USER_GID}" "${USERNAME}"; \
        useradd -m -s /usr/bin/zsh -u "${USER_UID}" -g "${USER_GID}" "${USERNAME}"; \
    fi

USER ${USERNAME}

ENV WORKSPACE="/home/${USERNAME}/adore"
WORKDIR ${WORKSPACE}

ENV CCACHE_DIR="${WORKSPACE}/.cache/ccache" \
    CC="/usr/lib/ccache/gcc" \
    CXX="/usr/lib/ccache/g++"

CMD ["/bin/bash"]
