---
title: Automatically secure NGINX with Let's Encrypt and Ansible
keywords:
  - blog
  - nginx
  - ansible
date: July 5, 2019
---

Recently I've gotten a new server and I wanted to move my blog on there. The
blog more or less runs entirely on NGINX, should be served via HTTPS, and should
be set up entirely via Ansible (including certificates), so I started wiring up
my Ansible roles.

The overall procedure is the following:

- install nginx
- configure nginx together with certbot
- ask [Let's Encrypt](https://letsencrypt.org) for certificates
- configure HTTPS virtual hosts

This seems like the simplest way to go about things. Note that my servers run
Debian, therefore your mileage may vary on other distributions, although the
general process should stay the same. I wrote three Ansible roles for this:

## role *nginx* - install nginx

Installing a package in Ansible is as straightforward as it gets:

```yml
# roles/nginx/tasks/main.yml
- name: ensure nginx is installed
  package:
    name: nginx
    state: present
```

Make sure to allow port 80 and 443 through your firewall such that NGINX is
reachable from the world wide web.

## role *nginx-letsencrypt* - configure certbot with nginx

This role is a bit more interesting, since it sets up most of the prerequisites
for serving certificate requests. The renewal hook is important as otherwise
nginx might be sitting around with expired certificates even though certbot has
already renewed them at some point.

```yml
# roles/nginx-letsencrypt/tasks/main.yml
- name: ensure certbot is installed
  package:
    name: certbot
    state: present

- name: ensure `/etc/nginx/letsencrypt.conf` is up-to-date
  template:
    src: letsencrypt.conf.j2
    dest: /etc/nginx/letsencrypt.conf
    owner: root
    group: root
    mode: 0444

- name: ensure the renewal hook directory exists
  file:
    path: /etc/letsencrypt/renewal-hooks/deploy/
    state: directory
    owner: root
    group: root
    mode: 0500

- name: ensure nginx is reloaded on certificate renewal
  copy:
    content: |
      #!/bin/sh
      set -ex

      systemctl reload nginx
    dest: /etc/letsencrypt/renewal-hooks/deploy/reload-nginx
    owner: root
    group: root
    mode: 0500
```

The template `letsencrypt.conf.j2` is a simple nginx location block which I use
in just about every website using this setup, therefore it is included in the
nginx directory. The contents, without my comments:

```nginx
# roles/nginx-letsencrypt/templates/letsencrypt.conf.j2
location ^~ /.well-known/acme-challenge/ {
    root {{ nginx_letsencrypt_webroot_path }};
}
```

The variable `nginx_letsencrypt_webroot_path` is defaulted to
`/var/www/_letsencrypt` in my setup, set it as you wish.

This role also contains a second task, call it `setup-certificate.yml`, which is
intended for inclusion in roles that want to ensure they have a certificate. The
contents are as follows:

```yml
# roles/nginx-letsencrypt/tasks/setup-certificate.yml
- name: ensure the webroot exists
  file:
    path: "{{ nginx_letsencrypt_webroot_path }}"
    state: directory
    owner: root
    group: www-data
    mode: 0750

- name: ensure we have a certificate
  command: >
    /usr/bin/certbot
    --agree-tos
    --non-interactive
    --email {{ nginx_letsencrypt_email }}
    --authenticator webroot
    --webroot-path {{ nginx_letsencrypt_webroot_path | quote }}
    --domains {{ nginx_letsencrypt_domains | join(',') | quote }}
    certonly
  args:
    creates: /etc/letsencrypt/live/{{ nginx_letsencrypt_domains[0] }}
```

## role *personal-website* - hook up everything else

This role depends on the other two and mixes them together to configure the
vhosts in nginx. Ignoring specific stuff such as copying static files to this
website or also setting up a `www.{mydomain}` vhost is left out here for
brevity.

```yml
# roles/personal-website/tasks/main.yml
- name: ensure the HTTP vhost is up-to-date
  template:
    src: example.com.http.conf.j2
    dest: /etc/nginx/conf.d/example.com.http.conf
    owner: root
    group: root
    mode: 0444
  notify:
    # Provided by the `nginx` role.
    - reload nginx

# Ensure we flush handlers here so that NGINX can handle
# the webroot challenge from Let's Encrypt in case the HTTP
# virtual hosts were just added in the previous task.
- meta: flush_handlers

# Include the `nginx-letsencrypt` role to fetch
# certificates via the webroot authenticator.
- name: ensure Let's Encrypt certificates are set up
  include_role:
    name: nginx-letsencrypt
    tasks_from: setup-certificate.yml
  vars:
    nginx_letsencrypt_email: robert@example.com
    nginx_letsencrypt_domains:
      - example.com

# Now that we have certificates, we can wire up the HTTPS virtual hosts.
- name: ensure the HTTPS vhost is up-to-date
  template:
    src: example.com.https.conf.j2
    dest: /etc/nginx/conf.d/example.com.https.conf
    owner: root
    group: root
    mode: 0444
  notify:
    - reload nginx
```

.. which concludes the roles. The `certbot` Debian package includes a systemd timer
which refreshes your old certificates, and if that does not work, Let's Encrypt
will send you an E-Mail to the address you specified above.


<!-- vim: set textwidth=80 sw=2 ts=2: -->
