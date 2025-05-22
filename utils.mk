
.PHONY: save
save: save_docker_images

.PHONY: load_docker_images
load: load_docker_images

.PHONY: debug
debug:
	docker exec -it -u root $(shell make container_name_adore_cli) /bin/bash

.PHONY: check_deployment_host_connection
check_deployment_host_connection:
	@echo "  checking connection..."
	@ping -c 1 "$$(echo $${DEPLOY_HOST} | sed 's/^[^@]*@//')" >/dev/null 2>&1 || { echo "ERROR: Deployment host is unreachable." >&2; exit 1; }
	@echo "  Deployment host: ${DEPLOY_HOST} host is reachable."

.PHONY: check_deployment_ssh_keys
check_deployment_ssh_keys:
	@echo "  checking ssh keys for deployment host: ${DEPLOY_HOST} ..."
	@ssh -o BatchMode=yes -o ConnectTimeout=5 "$(DEPLOY_HOST)" 'exit' || { echo "ERROR: SSH keys are not set up. Configure ssh keys and try again." >&2; exit 1; }
	@echo "  ssh keys configured for deployment host: ${DEPLOY_HOST} ..."

.PHONY: check_rsync
check_rsync:
	@command -v rsync >/dev/null 2>&1 || { echo >&2 "ERROR: rsync is not installed, install rsync and try again."; exit 1; }

.PHONY: check_deploy_host

check_deploy_host:
	@if [ -z "$$DEPLOY_HOST" ]; then \
	    echo "ERROR: DEPLOY_HOST env var is not set. Please set DEPLOY_HOST env var and try again." >&2; \
	    exit 1; \
	fi;
	@echo "Using deployment host: $${DEPLOY_HOST}"


.PHONY: deploy
deploy: check_rsync check_deploy_host check_deployment_host_connection check_deployment_ssh_keys
	@DEPLOY_DIR=$${DEPLOYMENT_DIRECTORY:-"~/adore"}; \
	if ssh $(DEPLOY_HOST) "[ ! -d '$$DEPLOY_DIR' ]"; then \
	    echo "  Deploying adore to $${DEPLOY_HOST}:$$DEPLOY_DIR:"; \
	    cd ../ && rsync -avz --progress adore/ $${DEPLOY_HOST}:$$DEPLOY_DIR; \
	    ssh $(DEPLOY_HOST) "cd '$$DEPLOY_DIR' && make load"; \
	else \
	    echo "  Deployment directory: \"$$DEPLOY_DIR\" already exists on remote host ${DEPLOY_HOST}. Skipping rsync."; \
	fi;

.PHONY: connect_deploy
connect_deploy: check_deploy_host check_deployment_ssh_keys
	@echo "Connecting to $(DEPLOY_HOST)..."
	@if ssh -q -o "BatchMode=yes" $(DEPLOY_HOST) "exit"; then \
		echo "Checking for zsh on the remote host..."; \
		if ssh $(DEPLOY_HOST) '[ -x "/usr/bin/zsh" ]'; then \
			echo "Zsh is available on the remote host."; \
			ssh -t $(DEPLOY_HOST) 'cd "${DEPLOYMENT_DIRECTORY:-~/adore}" && /usr/bin/zsh -l'; \
		else \
			echo "Zsh is not available, falling back to bash."; \
			ssh -t $(DEPLOY_HOST) 'cd "${DEPLOYMENT_DIRECTORY:-~/adore}" && /bin/bash -l'; \
		fi \
	else \
		echo "SSH connection failed or remote host is unavailable."; \
	fi

.PHONY: nmap
nmap:
	nmap -sP $(shell ip -o -4 addr show up | awk '/(eth|enp|wlo)[0-9]/ && !/veth/ {sub(/\/.*/, "", $$4); print $$4"/24"}')

.PHONY: package
package:
	echo "${ADORE_TAG}"
	cd ../ && tar -czvf adore_${ADORE_TAG}.tar.gz adore
	mkdir -p build
	mv ../adore_${ADORE_TAG}.tar.gz build/
