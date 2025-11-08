# .docker/ci/Dockerfile
FROM adore_base:latest

# -------------------------------------------------------------------
# CI-specific system dependencies (docs, test tooling, etc.)
# -------------------------------------------------------------------
COPY .docker/deps/apt.ci.txt /tmp/apt.ci.txt
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
COPY .docker/deps/pip.ci.txt /tmp/pip.ci.txt
RUN if [ -s /tmp/pip.ci.txt ]; then \
      pip3 install --no-cache-dir --break-system-packages --ignore-installed -r /tmp/pip.ci.txt && \
      rm -f /tmp/pip.ci.txt; \
    else \
      echo "No CI pip dependencies listed in /tmp/pip.ci.txt"; \
    fi


# CI user (still UID/GID mapped so volume permissions behave)
ARG CI_USERNAME=ci
ARG CI_USER_UID=2001
ARG CI_USER_GID=2001

RUN set -eux; \
    existing_user="$(getent passwd "${CI_USER_UID}" | cut -d: -f1 || true)"; \
    if [ -n "${existing_user}" ]; then \
        echo "Renaming user ${existing_user} to ${CI_USERNAME}"; \
        usermod -l "${CI_USERNAME}" "${existing_user}"; \
        usermod -d "/home/${CI_USERNAME}" -m "${CI_USERNAME}"; \
        groupmod -n "${CI_USERNAME}" "${existing_user}"; \
    else \
        echo "Creating new CI user ${CI_USERNAME}"; \
        groupadd -g "${CI_USER_GID}" "${CI_USERNAME}"; \
        useradd -m -s /bin/bash -u "${CI_USER_UID}" -g "${CI_USER_GID}" "${CI_USERNAME}"; \
    fi

USER ${CI_USERNAME}

ENV WORKSPACE="/home/${CI_USERNAME}/adore"
WORKDIR ${WORKSPACE}

ENV CCACHE_DIR="${WORKSPACE}/.cache/ccache" \
    CC="/usr/lib/ccache/gcc" \
    CXX="/usr/lib/ccache/g++"

CMD ["/bin/bash"]
