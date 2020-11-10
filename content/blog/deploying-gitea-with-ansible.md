---
title: Deploying Gitea with Ansible
keywords:
  - gitea
  - ansible
  - devops
date: November 10, 2020
---

If you want to host a simple and lightweight git server along with a pretty web
interface, [Gitea](https://gitea.io/en-us/) is the way to go. After setting up
[blog deployment via
Ansible](https://github.com/jchristgit/personal-website/blob/master/deploy.yml),
I set out to write a deployment for a personal Gitea server.

All ``.yaml`` files of the final deployment role can be found at the end of this
page.

Since Gitea is contained within a single binary, deployment for the server
itself will be as follows:

- Installing the binary
- Configuring a [systemd
  service](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- Configuring the Gitea service

We will also set up a dedicated user to run the server.


## Binary installation

To start things off, we will clone the binary from the [GitHub
repository](https://github.com/go-gitea/gitea). We set two variables with the
download URL and a SHA256 checksum:

```yml
# roles/gitea/defaults/main.yml
gitea_binary_download_url: https://github.com/go-gitea/gitea/releases/download/v1.12.5/gitea-1.12.5-linux-amd64
gitea_binary_checksum: sha256:8ed8bff1f34d8012cab92943214701c10764ffaca102e311a3297edbb8fce940
```

The builtin ``get_url`` module will then manage installing the binary:

```yml
# roles/gitea/tasks/main.yml
- name: install the binary
  get_url:
    url: "{{ gitea_binary_download_url }}"
    checksum: "{{ gitea_binary_checksum }}"
    dest: /usr/local/bin/gitea
    owner: root
    group: root
    mode: 0555
  notify:
    - restart the gitea service
```

Note that we hook up a
[handler](https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html)
to restart the Gitea service in case the binary changed. The handler definition
simply uses the systemd service we are about to define:

```yml
# roles/gitea/handlers/main.yml
- name: restart the gitea service
  service:
    name: gitea.service
    state: restarted
```


## Service user and configuration directory

Before we configure the systemd service, we set up a dedicated system user to
run the service and store its data. The home directory is configured into the
standard location for service state, which conveniently saves us from setting it
up separately. A configuration directory for gitea itself is also created:

```yml
# roles/gitea/tasks/main.yml
- name: create the service user
  user:
    name: gitea
    state: present
    system: true
    home: /var/lib/gitea

- name: create the configuration directory
  file:
    path: /etc/gitea
    state: directory
    owner: gitea
    group: root
    mode: 0500
```

Note that we grant the `gitea` user write permissions on the configuration
directory. This is intentional, as Gitea will write the configuration file on
initial startup, even if already properly configured.


## Server configuration

Our
[``template``](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html)
task will use two rarely used options, ``variable_start_string`` and
``variable_end_string``, in order to set different templating tokens. We need to
add these, as Gitea uses ``{{`` and ``}}`` itself, which would otherwise
conflict with the module:

```yml
# roles/gitea/tasks/main.yml
- name: template the configuration
  template:
    src: app.ini.j2
    dest: /etc/gitea/app.ini
    owner: gitea
    group: root
    # gitea needs rw permissions to this on first launch
    mode: 0600
    variable_start_string: ((
    variable_end_string: ))
  notify:
    - restart the gitea service
```

To retrieve a sample configuration file, I started the service and copied the
configuration file that was written. If you take the example configuration file
from the documentation, it is likely that Ansible will make changes every time
you deployment, ruining your diffs. That's inconvenient!

For brevity I will not include the entire configuration file here. I've added
the following variables, which contain both the sections & option names of the
configuration file, making them easy to find:

```ini
# result of ``:g/((  `` on ``roles/gitea/templates/app.ini.j2``
APP_NAME = (( gitea_cfg_app_name ))
DOMAIN                          = (( gitea_cfg_server_domain ))
HTTP_ADDR                       = (( gitea_cfg_server_http_addr ))
START_SSH_SERVER                = (( gitea_cfg_server_start_ssh_server ))
SSH_PORT                        = (( gitea_cfg_server_ssh_port ))
SSH_LISTEN_PORT                 = (( gitea_cfg_server_ssh_listen_port ))
SECRET_KEY                               = (( gitea_cfg_security_secret_key ))
INTERNAL_TOKEN                           = (( gitea_cfg_security_internal_token ))
```

I recommend that you keep ``gitea_cfg_security_secret_key`` and
``gitea_cfg_security_internal_token`` in [Ansible
Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html).


## Systemd service configuration

Now that we have configured the Gitea server itself, we need to configure the
systemd service. This is accomplished with another ``template`` task:

```yml
# roles/gitea/defaults/main.yml
- name: template the service file
  template:
    src: gitea.service.j2
    dest: /etc/systemd/system/gitea.service
    owner: root
    group: root
  register: gitea_service_file_task
  notify:
    - restart the gitea service
```

The service file is, at its core, rather simple:

```ini
# roles/gitea/templates/gitea.service.j2

[Unit]
Description=self-hosted git service
Documentation=https://docs.gitea.io/en-us/

[Service]
User=gitea
Group=gitea
RuntimeDirectory=gitea
StateDirectory=gitea
StateDirectoryMode=0700
ExecStart=/usr/local/bin/gitea -c /etc/gitea/app.ini
WorkingDirectory=/var/lib/gitea

[Install]
WantedBy=network-online.target
```

My service file has a bit more content in order to sandbox the service. This is
not required, but I believe it is good practice to use systemd's sandboxing
capabilities. You can find the complete options at the end of this post.

Note that we ``register`` the task output to reuse it in the upcoming service
start task:

```yml
# roles/gitea/defaults/main.yml
- name: enable and start gitea
  service:
    name: gitea.service
    state: started
    enabled: true
    daemon_reload: "{{ gitea_service_file_task is changed }}"
```

That wraps up the content of the ``gitea`` role. Set variables, deploy it on
your server of choice and enjoy your self-hosted git server! Feel free to send
me an e-mail if you have any questions.


## Further steps

My deployment goes a bit further than just deploying the Gitea binary. I use my
``nginx-letsencrypt`` role from [Automatically secure NGINX with Let's Encrypt
and Ansible](./automatically-secure-nginx-with-letsencrypt-and-ansible.html) in
order to first retrieve SSL certificates, then another role called
``gitea-nginx`` to configure the Gitea virtual host in nginx and allow SSH
traffic through the firewall.


## Complete role contents

As promised, here are the complete contents of each file in my role:

<details>
  <summary>``roles/gitea/handlers/main.yml``</summary>
```yml
---
- name: restart the gitea service
  service:
    name: gitea.service
    state: restarted
```
</details>

<details>
  <summary>``roles/gitea/defaults/main.yml``</summary>
```yml
---
## binary download options
gitea_binary_download_url: https://github.com/go-gitea/gitea/releases/download/v1.12.5/gitea-1.12.5-linux-amd64
gitea_binary_checksum: sha256:8ed8bff1f34d8012cab92943214701c10764ffaca102e311a3297edbb8fce940

## service configuration
# resource control
gitea_svc_cpu_quota: 50%
gitea_svc_memory_low: 75M
gitea_svc_memory_high: 230M
gitea_svc_memory_max: 250M
gitea_svc_tasks_max: 50

## gitea configuration file
# top-level options
gitea_cfg_app_name: 'jc : gitea'

# [server]
gitea_cfg_server_http_addr: 127.0.0.1
gitea_cfg_server_domain: git.(( ansible_fqdn ))
gitea_cfg_server_start_ssh_server: false
gitea_cfg_server_ssh_port: 22
gitea_cfg_server_ssh_listen_port: "(( gitea_cfg_server_ssh_port ))"

# [security]
gitea_cfg_security_secret_key: "(( lookup('password', 'secrets/' + ansible_nodename + '/gitea/secret_key') ))"
```
</details>

<details>
  <summary>``roles/gitea/tasks/main.yml``</summary>
```yml
---
# This task is included here for completeness, but I expect
# ``git`` to already # be present on most systems.
- name: install git
  package:
    name: git-core
    state: present

- name: install the binary
  get_url:
    url: "{{ gitea_binary_download_url }}"
    checksum: "{{ gitea_binary_checksum }}"
    dest: /usr/local/bin/gitea
    owner: root
    group: root
    mode: 0555
  notify:
    - restart the gitea service

- name: template the service file
  template:
    src: gitea.service.j2
    dest: /etc/systemd/system/gitea.service
    owner: root
    group: root
  register: gitea_service_file_task
  notify:
    - restart the gitea service

- name: create the service user
  user:
    name: gitea
    state: present
    system: true
    home: /var/lib/gitea

- name: create the configuration directory
  file:
    path: /etc/gitea
    state: directory
    owner: gitea
    group: root
    mode: 0500

- name: template the configuration
  template:
    src: app.ini.j2
    dest: /etc/gitea/app.ini
    owner: gitea
    group: root
    # gitea needs rw permissions to this on first launch
    mode: 0600
    variable_start_string: ((
    variable_end_string: ))
  notify:
    - restart the gitea service

- name: enable and start gitea
  service:
    name: gitea.service
    state: started
    enabled: true
    daemon_reload: "{{ gitea_service_file_task is changed }}"

# vim: sw=2 ts=2:
```
</details>

<details>
  <summary>``roles/gitea/templates/gitea.service.j2``</summary>
```ini
# {{ ansible_managed }}

[Unit]
Description=self-hosted git service
Documentation=https://docs.gitea.io/en-us/

[Service]
User=gitea
Group=gitea
RuntimeDirectory=gitea
StateDirectory=gitea
StateDirectoryMode=0700
ExecStart=/usr/local/bin/gitea -c /etc/gitea/app.ini
WorkingDirectory=/var/lib/gitea

# Comment out the following if your Gitea does not need external internet access
# and the only clients connecting are from localhost (such as your reverse proxy).
# The following features may not work properly when using these settings:
#   - Repository mirroring
#   - External authorization providers
# IPAddressAllow=localhost
# IPAddressDeny=any

CapabilityBoundingSet=
LockPersonality=true
MemoryDenyWriteExecute=true
NoNewPrivileges=true
PrivateDevices=true
PrivateTmp=true
PrivateUsers=true
ProtectControlGroups=true
ProtectHome=true
ProtectKernelModules=true
ProtectKernelTunables=true
ProtectSystem=strict
RemoveIPC=true
RestrictAddressFamilies=AF_INET
RestrictNamespaces=true
RestrictRealtime=true
SystemCallArchitectures=native
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources
UMask=0077


# REVIEW: only needs access to /etc/gitea. use tmpfs for /etc, bind mount over
#   systemd-run -t -p TemporaryFileSystem=/etc:ro -p BindReadOnlyPaths=/etc/gitea/ bash
ReadWritePaths=/etc/gitea/app.ini
ReadWritePaths=/var/lib/gitea

# Resource control.
CPUAccounting=true
CPUQuota={{ gitea_svc_cpu_quota }}
MemoryAccounting=true
MemoryLow={{ gitea_svc_memory_low }}
MemoryHigh={{ gitea_svc_memory_high }}
MemoryMax={{ gitea_svc_memory_max }}
TasksAccounting=true
TasksMax={{ gitea_svc_tasks_max }}

[Install]
WantedBy=network-online.target

# vim: ft=dosini.jinja2:
```
</details>


Sorry, I did not include ``app.ini.j2`` here, since it changes over the course
of releases, and is also about the size of my entire website.

<!-- vim: set textwidth=80 sw=2 ts=2 spell: -->
