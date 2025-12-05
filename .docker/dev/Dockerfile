# .docker/dev/Dockerfile
FROM adore_base:latest

# Dev-only APT deps (shell candy, X11, tracing, etc.)
COPY .docker/dev/apt.dev.txt /tmp/apt.dev.txt

RUN apt-get update && \
    xargs -r -a /tmp/apt.dev.txt apt-get install -y && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Helix editor
RUN curl -L https://github.com/helix-editor/helix/releases/download/25.01.1/helix-25.01.1-x86_64-linux.tar.xz \
    | tar -xJ && \
    mv helix-25.01.1-x86_64-linux /opt/helix && \
    ln -s /opt/helix/hx /usr/local/bin/hx && \
    echo "export HELIX_RUNTIME=/opt/helix/runtime" >> /etc/profile

# User setup (UID/GID mapping)
ARG USERNAME=developer
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
ENV IN_ADORE_DOCKER=1

# Oh My Zsh (non-interactive)
ENV RUNZSH=no \
    CHSH=no

RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Workspace + ccache
ENV WORKSPACE="/home/${USERNAME}/adore"
WORKDIR ${WORKSPACE}

ENV CCACHE_DIR="${WORKSPACE}/.cache/ccache" \
    CC="/usr/lib/ccache/gcc" \
    CXX="/usr/lib/ccache/g++"

# Zsh history & QoL
RUN echo '\
export HISTFILE=~/adore/.zsh_history\n\
export HISTSIZE=100000\n\
export SAVEHIST=100000\n\
setopt HIST_IGNORE_DUPS\n\
setopt HIST_REDUCE_BLANKS\n\
setopt SHARE_HISTORY\n\
setopt INC_APPEND_HISTORY\n\
' >> "/home/${USERNAME}/.zshrc" && \
    mkdir -p "${WORKSPACE}" && \
    touch "${WORKSPACE}/.zsh_history" && \
    chown -R "${USERNAME}:${USERNAME}" "${WORKSPACE}"

# --- ADORe: auto-source ROS + workspace in interactive zsh shells ---
RUN set -eux; \
    ZSHRC="$HOME/.zshrc"; \
    touch "$ZSHRC"; \
    { \
      echo ''; \
      echo '# --- ADORe ROS environment -----------------------------------------'; \
      echo '# Source the chosen ROS distro (defaults to jazzy if ROS_DISTRO unset)'; \
      echo 'if [ -f "/opt/ros/${ROS_DISTRO:-jazzy}/setup.zsh" ]; then'; \
      echo '  source "/opt/ros/${ROS_DISTRO:-jazzy}/setup.zsh"'; \
      echo 'fi'; \
      echo ''; \
      echo '# Source local colcon workspace overlay if it exists'; \
      echo 'if [ -f "$HOME/adore/.colcon_workspace/install/local_setup.zsh" ]; then'; \
      echo '  source "$HOME/adore/.colcon_workspace/install/local_setup.zsh"'; \
      echo 'elif [ -f "$HOME/adore/.colcon_workspace/install/setup.zsh" ]; then'; \
      echo '  source "$HOME/adore/.colcon_workspace/install/setup.zsh"'; \
      echo 'fi'; \
      echo 'if [[ -n "$IN_ADORE_DOCKER" ]]; then'; \
      echo '  PROMPT="%F{green}[ADORe-DEV]%f ${PROMPT}"'; \
      echo 'fi'; \
    } >> "$ZSHRC"

CMD ["/usr/bin/zsh", "-l"]
