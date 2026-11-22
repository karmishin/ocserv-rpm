# ocserv for EL9

RPM packaging of [ocserv](https://ocserv.openconnect-vpn.net/) for
AlmaLinux / Rocky / RHEL 9, for x86_64 and aarch64.

## Install

Download the RPM for your architecture and `RPM-GPG-KEY-ocserv` from the
[Releases](../../releases) page.

```bash
gpg --show-keys RPM-GPG-KEY-ocserv
rpm --import RPM-GPG-KEY-ocserv
rpm -K ocserv-1.6.0-1.1.el9.$(uname -m).rpm
dnf install -y epel-release
dnf install -y ./ocserv-1.6.0-1.1.el9.$(uname -m).rpm
```

To keep EPEL's older ocserv from replacing this build:

```bash
dnf config-manager --save --setopt=epel.excludepkgs=ocserv
```

## Differences from Fedora's spec

This package is based on 
[Fedora rawhide's meson spec](https://src.fedoraproject.org/rpms/ocserv/blob/19aceb80f8e603abe2606394646dd6d52fc71c2d/f/ocserv.spec).
- OIDC auth enabled
- Bundled `llhttp`
- Prebuilt man pages from the tarball
- `ocserv` user is created with `%sysusers_create_compat`
- `openpgpverify` is replaced with `%gpgverify`
- Dropped `pam-guard-page.patch` (already in 1.6.0)
- `Release: 1.1%{?dist}`, so this build wins over an EPEL build of the same
  version
- The `dbip-lite-*` recommendation is dropped, because those packages don't
  exist for EL9

## Building

```bash
dnf install -y epel-release dnf-plugins-core rpm-build rpmdevtools
dnf config-manager --set-enabled crb
spectool -g -C SOURCES SPECS/ocserv.spec
dnf builddep -y SPECS/ocserv.spec
rpmbuild -ba --define "_sourcedir $PWD/SOURCES" SPECS/ocserv.spec
```
