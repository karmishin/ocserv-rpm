# ocserv for EL9 (AlmaLinux / Rocky / RHEL 9).
#
# Based on Fedora's rawhide spec:
# https://src.fedoraproject.org/rpms/ocserv/blob/19aceb80f8e603abe2606394646dd6d52fc71c2d/f/ocserv.spec
#
# Build options:  --without check     skip the test suite
#                 --without oidc      build without OpenID Connect support
#                 --with root_tests   also run the tests that need root, netns and
#                                     a working tun device (CAP_SYS_ADMIN +
#                                     CAP_NET_ADMIN)

%bcond_without check
%bcond_without oidc
%bcond_with root_tests

%global _hardened_build 1

# SHA-512 of Source0; checked in %%prep before the signature.
%global tarball_sha512 512d882b025d157023d0d658a19fbc5f9ecbee9949cd43f3e785e694c97c8c21200a396a64b8990bd9d332e713bfd85e4b2935969755280864b5bc73520f740c

Name:		ocserv
Version:	1.6.0
# .1 so this build wins over an EPEL build of the same version (which would
# lack OIDC); any newer upstream version from EPEL still takes precedence.
Release:	1.1%{?dist}
Summary:	OpenConnect SSL VPN server

# For a breakdown of the licensing, see PACKAGE-LICENSING
License:	GPL-2.0-or-later AND BSD-3-Clause AND MIT AND CC0-1.0
URL:		https://ocserv.openconnect-vpn.net/
Source0:	https://www.infradead.org/ocserv/download/%{name}-%{version}.tar.xz
Source1:	https://www.infradead.org/ocserv/download/%{name}-%{version}.tar.xz.sig
Source2:	gpgkey-1F42418905D8206AA754CCDC29EE58B996865171.gpg
Source3:	ocserv.conf
Source4:	ocserv.service
Source5:	ocserv-pamd.conf
Source6:	PACKAGE-LICENSING
Source8:	ocserv-genkey
Source9:	ocserv-script
Source11:	ocserv.sysusers
# (Fedora's pam-guard-page.patch is already part of the 1.6.0 tarball.)

# Test-only: the syslog LD_PRELOAD shim misses __syslog_chk() under
# -D_FORTIFY_SOURCE, failing test-cert-opt-pass in distro builds.
Patch0:		ocserv-syslog-shim-fortify.patch

BuildRequires:	gcc
BuildRequires:	meson
BuildRequires:	gnupg2
BuildRequires:	systemd-rpm-macros
BuildRequires:	libxcrypt-devel
BuildRequires:	gnutls-devel
BuildRequires:	nettle-devel
BuildRequires:	pam-devel
BuildRequires:	protobuf-c-devel
BuildRequires:	libnl3-devel, krb5-devel, libtasn1-devel, gperf, libtalloc-devel
BuildRequires:	libev-devel, radcli-devel, lz4-devel, readline-devel
BuildRequires:	libmaxminddb-devel
BuildRequires:	systemd, systemd-devel
BuildRequires:	liboath-devel
BuildRequires:	libseccomp-devel
%if %{with oidc}
BuildRequires:	cjose-devel, jansson-devel, libcurl-devel
%endif
%if %{with check}
BuildRequires:	iproute, ipcalc, openconnect, gnutls-utils
BuildRequires:	jq, nftables, nmap-ncat, iperf3, iputils
# without these the PAM tests (test-pam*, test-pass-pam-acct) aren't even
# registered. test-gssapi* still skips: gssntlmssp isn't available for EL9.
BuildRequires:	pam_wrapper, nss_wrapper
%if %{with root_tests}
# test-replay and haproxy-proxyproto* skip without these, but when run as
# root they need netns + tun, so only pull them in for privileged builds
BuildRequires:	tcpdump, haproxy, vim-common
# radius* need a RADIUS server (radiusd), test-year-2038 needs faketime,
# ac-aes*-gcm-cipher check the openconnect version through pkg-config
BuildRequires:	freeradius, libfaketime, openconnect-devel
%endif
BuildRequires:	uid_wrapper
# Fedora skips socket_wrapper on aarch64 (seccomp concerns); on EL9 the full
# cwrap suite passes there, and test-oidc-code-flow requires it.
BuildRequires:	socket_wrapper
%endif

Recommends:	gnutls-utils
Recommends:	iproute
Recommends:	nftables
Recommends:	pam
# For occtl country resolution
Recommends:	libmaxminddb

Requires(pre):		shadow-utils
%{?systemd_requires}

#gnulib is bundled. See https://fedorahosted.org/fpc/ticket/174
Provides:	bundled(gnulib)
#CCAN is bundled. See https://fedorahosted.org/fpc/ticket/364
Provides:	bundled(bobjenkins-hash) bundled(ccan-container_of)
Provides:	bundled(ccan-htable) bundled(ccan-list)
Provides:	bundled(ccan-check_type) bundled(ccan-build_assert)
Provides:	bundled(pcl)
# Upstream's default. EPEL 9's llhttp is older (9.2.1) and its soname
# (libllhttp.so.<major>.<minor>) changes on minor upgrades.
Provides:	bundled(llhttp) = 9.4.1

%description
OpenConnect server (ocserv) is an SSL VPN server. Its purpose is to be a
secure, small, fast and configurable VPN server. It implements the OpenConnect
SSL VPN protocol, and has also (currently experimental) compatibility with
clients using the AnyConnect SSL VPN protocol. The OpenConnect VPN protocol
uses the standard IETF security protocols such as TLS 1.2, and Datagram TLS
to provide the secure VPN service.

%prep
# 1. Must be the exact tarball this spec was reviewed against (same SHA-512 as
#    Fedora's dist-git `sources` file). Update together with Version.
echo '%{tarball_sha512}  %{SOURCE0}' | sha512sum -c -
# 2. Must be signed by the upstream maintainer's release key: Nikos
#    Mavrogiannopoulos, 1F42 4189 05D8 206A A754 CCDC 29EE 58B9 9686 5171
#    (the same key Fedora and Debian ship; upstream's download page names 96865171).
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'

%autosetup -p1

%build
%meson \
	-Dlocal-llhttp=true \
	-Dsystemd=enabled \
%if %{with oidc}
	-Doidc-auth=enabled \
%endif
%if %{without check}
	-Dtests=false \
%endif
%if %{without root_tests}
	-Droot-tests=false \
	-Dtun-tests=false \
%endif
	%{nil}
%meson_build

%install
cp -a %{SOURCE6} PACKAGE-LICENSING
install -D -p -m 644 %{SOURCE5} %{buildroot}%{_sysconfdir}/pam.d/ocserv
install -D -p -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/ocserv/ocserv.conf
install -D -p -m 644 doc/profile.xml %{buildroot}%{_localstatedir}/lib/ocserv/profile.xml
install -D -p -m 755 %{SOURCE8} %{buildroot}%{_sbindir}/ocserv-genkey
install -D -p -m 755 %{SOURCE9} %{buildroot}%{_bindir}/ocserv-script
install -D -p -m 644 %{SOURCE4} %{buildroot}%{_unitdir}/ocserv.service
install -D -p -m 644 %{SOURCE11} %{buildroot}%{_sysusersdir}/ocserv.conf
%meson_install

%if %{with check}
%check
%meson_test
%endif

%pre
%sysusers_create_compat %{SOURCE11}
mkdir -p %{_sysconfdir}/pki/ocserv/public
mkdir -p -m 700 %{_sysconfdir}/pki/ocserv/private
mkdir -p %{_sysconfdir}/pki/ocserv/cacerts

%post
%systemd_post ocserv.service

%preun
%systemd_preun ocserv.service

%postun
%systemd_postun_with_restart ocserv.service

%files
%license COPYING PACKAGE-LICENSING
%license src/ccan/licenses/CC0 src/ccan/licenses/LGPL-2.1 src/ccan/licenses/BSD-MIT
%doc AUTHORS NEWS README.md doc/README-radius.md
%if %{with oidc}
%doc doc/README-oidc.md
%endif

%dir %{_localstatedir}/lib/ocserv
%dir %{_sysconfdir}/ocserv
%config(noreplace) %{_sysconfdir}/ocserv/ocserv.conf
%config(noreplace) %{_sysconfdir}/pam.d/ocserv
%config(noreplace) %{_localstatedir}/lib/ocserv/profile.xml

%{_mandir}/man8/ocserv.8*
%{_mandir}/man8/occtl.8*
%{_mandir}/man8/ocpasswd.8*

%{_bindir}/ocpasswd
%{_bindir}/occtl
%{_bindir}/ocserv-script
%{_libexecdir}/ocserv-fw
%{_sbindir}/ocserv
%{_sbindir}/ocserv-worker
%{_sbindir}/ocserv-genkey
%{_unitdir}/ocserv.service
%{_sysusersdir}/ocserv.conf

%changelog
* Sun Nov 22 2026 Mikhail Karmishin <mikhail@karmishin.com> - 1.6.0-1.1
- Update to 1.6.0 for EL9 (EPEL 9 is still on 1.4.1)
- Includes 1.5.0 security fixes: unauthenticated heap overflow via
  oversized webvpncontext cookie (#719), DTLS MTU integer underflow (#717)
- Port Fedora's meson-based spec to EL9; enable OIDC auth
- Drop pam-guard-page.patch (upstream); add syslog-shim __syslog_chk test fix
- Use socket_wrapper on aarch64 too
- Use the bundled llhttp 9.4.1 instead of EPEL's 9.2.1
