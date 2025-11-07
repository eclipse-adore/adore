FROM ros:jazzy-ros-base

# --- Environment Setup ---
ENV LANG="C.UTF-8"
ENV LC_ALL="C.UTF-8"

# --- Copy and Install System Dependencies ---
COPY .docker/minimal/apt_requirements.txt /tmp/apt_requirements.txt

RUN apt update && \
    xargs -a /tmp/apt_requirements.txt apt install -y && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# --- Python Dependencies ---
COPY .docker/minimal/pip_requirements.txt /tmp/pip_requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/pip_requirements.txt

# --- Install Helix Editor (Prebuilt Binary) ---
RUN curl -L https://github.com/helix-editor/helix/releases/download/25.01.1/helix-25.01.1-x86_64-linux.tar.xz \
    | tar -xJ && \
    mv helix-25.01.1-x86_64-linux /opt/helix && \
    ln -s /opt/helix/hx /usr/local/bin/hx && \
    echo "export HELIX_RUNTIME=/opt/helix/runtime" >> /etc/profile


# --- User Setup ---
ARG USERNAME=developer
ARG USER_UID=2001
ARG USER_GID=2001

RUN set -eux; \
    existing_user=$(getent passwd ${USER_UID} | cut -d: -f1 || true); \
    if [ -n "$existing_user" ]; then \
        echo "Renaming user $existing_user to ${USERNAME}"; \
        usermod -l ${USERNAME} $existing_user; \
        usermod -d /home/${USERNAME} -m ${USERNAME}; \
        groupmod -n ${USERNAME} $existing_user; \
    else \
        echo "Creating new user ${USERNAME}"; \
        groupadd -g ${USER_GID} ${USERNAME}; \
        useradd -m -s /usr/bin/zsh -u ${USER_UID} -g ${USER_GID} ${USERNAME}; \
    fi
    
USER ${USERNAME}

RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

ENV CCACHE_DIR="/home/${USERNAME}/adore/.cache/ccache"
ENV CC="/usr/lib/ccache/gcc"
ENV CXX="/usr/lib/ccache/g++"



# --- Switch to User and Working Directory ---
WORKDIR /home/${USERNAME}/adore
# --- Configure persistent Zsh history ---
RUN echo '\
export HISTFILE=~/adore/.zsh_history\n\
export HISTSIZE=100000\n\
export SAVEHIST=100000\n\
setopt HIST_IGNORE_DUPS\n\
setopt HIST_REDUCE_BLANKS\n\
setopt SHARE_HISTORY\n\
setopt INC_APPEND_HISTORY\n\
' >> /home/${USERNAME}/.zshrc && \
    touch /home/${USERNAME}/adore/.zsh_history && \
    chown ${USERNAME}:${USERNAME} /home/${USERNAME}/adore/.zsh_history
    
# --- Default Entry ---
CMD ["/usr/bin/zsh"]
