# Only enable if using patches that touches configure.ac,
# Makefile.am or other build system related files
#
%define enable_autoreconf 1

Summary: An authorization framework
Name: polkit
Version: 0.115
Release: 15%{?dist}
License: LGPLv2+
URL: http://www.freedesktop.org/wiki/Software/polkit
Source0: http://www.freedesktop.org/software/polkit/releases/%{name}-%{version}.tar.gz
Source1: http://www.freedesktop.org/software/polkit/releases/%{name}-%{version}.tar.gz.sign
Group: System Environment/Libraries


Patch1: polkit-0.115-bus-conn-msg-ssh.patch
Patch2: polkit-0.115-pkttyagent-auth-errmsg-debug.patch
Patch3: polkit-0.115-polkitagentlistener-res-leak.patch
Patch4: polkit-0.115-spawning-zombie-processes.patch
Patch5: polkit-0.115-CVE-2018-19788.patch
Patch6: polkit-0.115-CVE-2019-6133.patch
Patch7: polkit-0.115-pkttyagent-tty-echo-off-on-fail.patch
Patch8: polkit-0.115-allow-uid-of-1.patch
Patch9: polkit-0.115-move-to-mozjs60.patch
Patch10: polkit-0.115-jsauthority-memleak.patch
Patch11: polkit-0.115-pkttyagent-tcsaflush-batch-erase.patch
Patch12: polkit-0.115-CVE-2021-3560.patch
Patch13: polkit-0.115-CVE-2021-4034.patch
Patch14: polkit-0.115-CVE-2021-4115.patch
Patch15: polkit-0.115-tty-flags-restore-if-changed.patch


BuildRequires: gcc-c++
BuildRequires: glib2-devel >= 2.30.0
BuildRequires: expat-devel
BuildRequires: pam-devel
BuildRequires: gtk-doc
BuildRequires: intltool
BuildRequires: gobject-introspection-devel
BuildRequires: systemd, systemd-devel
BuildRequires: pkgconfig(mozjs-60)
BuildRequires: git

%if 0%{?enable_autoreconf}
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
%endif

Requires: dbus, polkit-pkla-compat
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

Requires(pre): shadow-utils
Requires(post): /sbin/ldconfig, systemd
Requires(preun): systemd
Requires(postun): /sbin/ldconfig, systemd

Obsoletes: PolicyKit <= 0.10
Provides: PolicyKit = 0.11

# polkit saw some API/ABI changes from 0.96 to 0.97 so require a
# sufficiently new polkit-gnome package
Conflicts: polkit-gnome < 0.97

Obsoletes: polkit-desktop-policy < 0.103
Provides: polkit-desktop-policy = 0.103

Obsoletes: polkit-js-engine < 0.110-4
Provides: polkit-js-engine = %{version}-%{release}

# when -libs was split out, handle multilib upgrade path -- rex
Obsoletes: polkit < 0.113-3

%description
polkit is a toolkit for defining and handling authorizations.  It is
used for allowing unprivileged processes to speak to privileged
processes.

%package devel
Summary: Development files for polkit
Group: Development/Libraries
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: %name-docs = %{version}-%{release}
Requires: glib2-devel
Obsoletes: PolicyKit-devel <= 0.10
Provides: PolicyKit-devel = 0.11

%description devel
Development files for polkit.

%package docs
Summary: Development documentation for polkit
Group: Development/Libraries
Requires: %name-devel = %{version}-%{release}
Obsoletes: PolicyKit-docs <= 0.10
Provides: PolicyKit-docs = 0.11
BuildArch: noarch

%description docs
Development documentation for polkit.

%package libs
Summary: Libraries for polkit
Group: Development/Libraries

%description libs
Libraries files for polkit.


%prep
%autosetup -S git

%build
%if 0%{?enable_autoreconf}
autoreconf -i
%endif
# we can't use _hardened_build here, see
# https://bugzilla.redhat.com/show_bug.cgi?id=962005
export CFLAGS='-fPIC %optflags'
export LDFLAGS='-pie -Wl,-z,now -Wl,-z,relro'
%configure --enable-gtk-doc \
        --disable-static \
        --enable-introspection \
        --disable-examples \
        --enable-libsystemd-login=yes
make V=1

%install
make install DESTDIR=$RPM_BUILD_ROOT INSTALL='install -p'

rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

%find_lang polkit-1

%pre
getent group polkitd >/dev/null || groupadd -r polkitd
getent passwd polkitd >/dev/null || useradd -r -g polkitd -d / -s /sbin/nologin -c "User for polkitd" polkitd
exit 0

%post
# The implied (systemctl preset) will fail and complain, but the macro hides
# and ignores the fact.  This is in fact what we want, polkit.service does not
# have an [Install] section and it is always started on demand.
%systemd_post polkit.service

%preun
%systemd_preun polkit.service

%postun
%systemd_postun_with_restart polkit.service

%files -f polkit-1.lang
%doc COPYING NEWS README
%{_datadir}/man/man1/*
%{_datadir}/man/man8/*
%{_datadir}/dbus-1/system-services/*
%{_unitdir}/polkit.service
%dir %{_datadir}/polkit-1/
%dir %{_datadir}/polkit-1/actions
%attr(0700,polkitd,root) %dir %{_datadir}/polkit-1/rules.d
%{_datadir}/polkit-1/actions/org.freedesktop.policykit.policy
%dir %{_sysconfdir}/polkit-1
%{_sysconfdir}/polkit-1/rules.d/50-default.rules
%attr(0700,polkitd,root) %dir %{_sysconfdir}/polkit-1/rules.d
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.PolicyKit1.conf
%{_sysconfdir}/pam.d/polkit-1
%{_bindir}/pkaction
%{_bindir}/pkcheck
%{_bindir}/pkttyagent
%dir %{_prefix}/lib/polkit-1
%{_prefix}/lib/polkit-1/polkitd

# see upstream docs for why these permissions are necessary
%attr(4755,root,root) %{_bindir}/pkexec
%attr(4755,root,root) %{_prefix}/lib/polkit-1/polkit-agent-helper-1

%files devel
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc
%{_datadir}/gir-1.0/*.gir
%{_includedir}/*
%{_datadir}/gettext/its/polkit.its
%{_datadir}/gettext/its/polkit.loc

%files docs
%{_datadir}/gtk-doc

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%files libs
%{_libdir}/lib*.so.*
%{_libdir}/girepository-1.0/*.typelib

%changelog
* Tue Nov 08 2022 Jan Rybar <jrybar@redhat.com> - 0.115-15
- pkttyagent gets stopped if killed in the background
- Resolves: rhbz#2128989

* Tue Feb 15 2022 Jan Rybar <jrybar@redhat.com> - 0.115-14
- file descriptor exhaustion (GHSL-2021-077)
- Resolves: CVE-2021-4115

* Fri Dec 03 2021 Jan Rybar <jrybar@redhat.com> - 0.115-13
- pkexec: argv overflow results in local privilege esc.
- Resolves: CVE-2021-4034

* Tue May 25 2021 Jan Rybar <jrybar@redhat.com> - 0.115-12
- early disconnection from D-Bus results in privilege esc.
- Resolves: CVE-2021-3560

* Mon Nov 04 2019 Jan Rybar <jrybar@redhat.com> - 0.115-11
- pkttyagent: resetting terminal erases rest of input line
- Resolves: rhbz#1757853

* Tue Oct 29 2019 Jan Rybar <jrybar@redhat.com> - 0.115-10
- Fix of jasuthority memleak
- Resolves: rhbz#1745918

* Tue Sep 10 2019 Jan Rybar <jrybar@redhat.com> - 0.115-9
- Rebuild to reflect mozjs60 s390 abi change
- Related: rhbz#1746889

* Thu Jun 13 2019 Jan Rybar <jrybar@redhat.com> - 0.115-8
- Backport changing dependency to mozjs60
- Resolves: rhbz#1729416

* Thu Jun 13 2019 Jan Rybar <jrybar@redhat.com> - 0.115-7
- pkttyagent: polkit-agent-helper-1 timeout leaves tty echo disabled
- Mitigation of regression caused by fix of CVE-2018-19788
- Resolves: rhbz#1693781
- Resolves: rhbz#1693814

* Mon Jan 21 2019 Jan Rybar <jrybar@redhat.com> - 0.115-6
- Fix of CVE-2019-6133, PID reuse via slow fork
- Resolves: rhbz#1667778

* Thu Dec 06 2018 Jan Rybar <jrybar@redhat.com> - 0.115-5
- Fix of CVE-2018-19788, priv escalation with high UIDs
- Resolves: rhbz#1656378

* Thu Aug 16 2018 Jan Rybar <jrybar@redhat.com> - 0.115-4
- Spawned zombie subprocesses not reaped
- Resolves: rhbz#1616282

* Fri Aug 10 2018 Jan Rybar <jrybar@redhat.com> - 0.115-3
- Resource leak found by static analyzer
- Resolves: rhbz#1602661

* Tue Aug 07 2018 Jan Rybar <jrybar@redhat.com> - 0.115-2
- Error message about getting authority is too elaborate (forward of #1342855)
- Bus disconnection report moved to debug mode (forward of #1249627)

* Tue Jul 10 2018 Miloslav Trmač <mitr@redhat.com> - 0.115-1
- Update to 0.115 (CVE-2018-1116)

* Tue Apr 03 2018 Ray Strode <rstrode@redhat.com> - 0.114-1
- Update to 0.114

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.113-16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.113-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.113-14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Apr 13 2017 Richard Hughes <rhughes@redhat.com> - 0.113-13
- Add the its files from upstream.

* Tue Apr 4 2017 Miloslav Trmač <mitr@redhat.com> - 0.113-12
- Fix a memory leak in PolkitPermission.
  Patch by Rui Matos <tiagomatos@gmail.com>
  Resolves: #1433915

* Tue Apr 4 2017 Miloslav Trmač <mitr@redhat.com> - 0.113-11
- Revert back to the state in 0.113-7, undoing the untested changes.

* Tue Apr  4 2017 Peter Robinson <pbrobinson@fedoraproject.org> 0.113-10
- Move to an upstream snapshot, rebase patches

* Fri Mar 31 2017 Rex Dieter <rdieter@fedoraproject.org> - 0.113-9
- restore Provides: polkit-desktop-policy polkit-js-engine

* Thu Mar 30 2017 Peter Robinson <pbrobinson@fedoraproject.org> 0.113-8
- Use %%license, license needs to be in -libs as it's the only guaranteed installed package
- Move to mozjs38
- Other upstream fixes
- Spec cleanups

* Mon Feb 13 2017 Miloslav Trmač <mitr@redhat.com> - 0.113-7
- Fix memory leaks when calling authentication agents
  Resolves: #1380166

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.113-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.113-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Jul 14 2015 Miloslav Trmač <mitr@redhat.com> - 0.113-4
- Bump the Obsoletes: to < 0.113-3 to account for the non-split 0.113-2.fc21
  Resolves: #1243004

* Sun Jul 12 2015 Rex Dieter <rdieter@fedoraproject.org> 0.113-3
- Obsoletes: polkit < 0.112-8 (handle multilib upgrade path)

* Fri Jul 10 2015 Miloslav Trmač <mitr@redhat.com> - 0.113-2
- Add a fully versioned dependency from polkit to polkit-libs
  Resolves: #1241759
- Require polkit-libs, not polkit, in polkit-devel

* Thu Jul 2 2015 Miloslav Trmač <mitr@redhat.com> - 0.113-1
- Update to polkit-0.113 (CVE-2015-3218, CVE-2015-3255, CVE-2015-3256,
  CVE-2015-4625)
  Resolves: #910262, #1175061, #1177930, #1194391, #1228739, #1233810

* Fri Jun 19 2015 Miloslav Trmač <mitr@redhat.com> - 0.112-11
- Add BuildRequires: systemd so that %%{_unitdir} is defined, to fix the build.

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.112-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sun Jan 25 2015 Rex Dieter <rdieter@fedoraproject.org>  - 0.112-9
- polkit doesn't release reference counters of GVariant data (#1180886)
- fix ldconfig scriptlets (move to -libs subpkg)

* Sat Nov 08 2014 Colin Walters <walters@redhat.com> - 0.112-8
- Split separate -libs package, so that NetworkManager can just depend on
  that, without dragging in the daemon (as well as libmozjs17).  This
  allows the creation of more minimal systems that want programs like NM,
  but do not need the configurability of the daemon; it would be ok if only
  root is authorized.

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.112-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Tue Jul 22 2014 Kalev Lember <kalevlember@gmail.com> - 0.112-6
- Rebuilt for gobject-introspection 1.41.4

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.112-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Jun  5 2014 Kay Sievers <kay@redhat.com> - 0.112-4
- backport upstream D-Bus "user bus" changes

* Mon Feb 10 2014 Miloslav Trmač <mitr@redhat.com> - 0.112-3
- Fix a PolkitAgentSession race condition
  Resolves: #1063193

* Sat Dec  7 2013 Miloslav Trmač <mitr@redhat.com> - 0.112-2
- Workaround pam_systemd setting broken XDG_RUNTIME_DIR
  Resolves: #1033774
- Always use mozjs-17.0 even if js-devel is installed

* Wed Sep 18 2013 Miloslav Trmač <mitr@redhat.com> - 0.112-1
- Update to polkit-0.112
- Resolves: #1009538, CVE-2013-4288

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.111-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed May 29 2013 Tomas Bzatek <tbzatek@redhat.com> - 0.111-2
- Fix a race on PolkitSubject type registration (#866718)

* Wed May 15 2013 Miloslav Trmač <mitr@redhat.com> - 0.111-1
- Update to polkit-0.111
  Resolves: #917888
- Use SpiderMonkey from mozjs17 instead of js
- Ship the signature in the srpm
- Try to preserve timestamps in (make install)

* Fri May 10 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-4
- Shut up rpmlint about Summary:
- Build with V=1
- Use %%{_unitdir} instead of hard-coding the path
- Use the new systemd macros, primarily to run (systemctl daemon-reload)
  Resolves: #857382

* Fri May 10 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-4
- Make the JavaScript engine mandatory.  The polkit-js-engine package has been
  removed, main polkit package Provides:polkit-js-engine for compatibility.
- Add Requires: polkit-pkla-compat
  Resolves: #908808

* Wed Feb 13 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-3
- Don't ship pk-example-frobnicate in the "live" configuration
  Resolves: #878112

* Fri Feb  8 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-2
- Own %%{_docdir}/polkit-js-engine-*
  Resolves: #907668

* Wed Jan  9 2013 David Zeuthen <davidz@redhat.com> - 0.110-1%{?dist}
- Update to upstream release 0.110

* Mon Jan  7 2013 Matthias Clasen <mclasen@redhat.com> - 0.109-2%{?dist}
- Build with pie and stuff

* Wed Dec 19 2012 David Zeuthen <davidz@redhat.com> 0.109-1%{?dist}
- Update to upstream release 0.109
- Drop upstreamed patches

* Thu Nov 15 2012 David Zeuthen <davidz@redhat.com> 0.108-3%{?dist}
- Attempt to open the correct libmozjs185 library, otherwise polkit
  authz rules will not work unless js-devel is installed (fdo #57146)

* Wed Nov 14 2012 David Zeuthen <davidz@redhat.com> 0.108-2%{?dist}
- Include gmodule-2.0 to avoid build error

* Wed Nov 14 2012 David Zeuthen <davidz@redhat.com> 0.108-1%{?dist}
- Update to upstream release 0.108
- Drop upstreamed patches
- This release dynamically loads the JavaScript interpreter and can
  cope with it not being available. In this case, polkit authorization
  rules are not processed and the defaults for an action - as defined
  in its .policy file - are used for authorization decisions.
- Add new meta-package, polkit-js-engine, that pulls in the required
  JavaScript bits to make polkit authorization rules work. The default
  install - not the minimal install - should include this package

* Wed Oct 10 2012 Adam Jackson <ajax@redhat.com> 0.107-4
- Don't crash if initializing the server object fails

* Tue Sep 18 2012 David Zeuthen <davidz@redhat.com> 0.107-3%{?dist}
- Authenticate as root if e.g. the wheel group is empty (#834494)

* Fri Jul 27 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.107-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jul 11 2012 David Zeuthen <davidz@redhat.com> 0.107-1%{?dist}
- Update to upstream release 0.107

* Fri Jun 29 2012 David Zeuthen <davidz@redhat.com> 0.106-2%{?dist}
- Add forgotten Requires(pre): shadow-utils

* Thu Jun 07 2012 David Zeuthen <davidz@redhat.com> 0.106-1%{?dist}
- Update to upstream release 0.106
- Authorizations are no longer controlled by .pkla files - from now
  on, use the new .rules files described in the polkit(8) man page

* Tue Apr 24 2012 David Zeuthen <davidz@redhat.com> 0.105-1%{?dist}
- Update to upstream release 0.105
- Nuke patches that are now upstream
- Change 'PolicyKit' to 'polkit' in summary and descriptions

* Thu Mar 08 2012 David Zeuthen <davidz@redhat.com> 0.104-6%{?dist}
- Don't leak file descriptors (bgo #671486)

* Mon Feb 13 2012 Matthias Clasen <mclasen@redhat.com> - 0.104-5%{?dist}
- Make the -docs subpackage noarch

* Mon Feb 06 2012 David Zeuthen <davidz@redhat.com> 0.104-4%{?dist}
- Set error if we cannot obtain a PolkitUnixSession for a given PID (#787222)

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.104-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Jan 03 2012 David Zeuthen <davidz@redhat.com> 0.104-2%{?dist}
- Nuke the ConsoleKit run-time requirement

* Tue Jan 03 2012 David Zeuthen <davidz@redhat.com> 0.104-1%{?dist}
- Update to upstream release 0.104
- Force usage of systemd (instead of ConsoleKit) for session tracking

* Tue Dec 06 2011 David Zeuthen <davidz@redhat.com> 0.103-1%{?dist}
- Update to upstream release 0.103
- Drop upstreamed patch
- Drop Fedora-specific policy, it is now upstream (fdo #41008)

* Wed Oct 26 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.102-3
- Rebuilt for glibc bug#747377

* Tue Oct 18 2011 David Zeuthen <davidz@redhat.com> 0.102-2%{?dist}
- Add patch to neuter the annoying systemd behavior where stdout/stderr
  is sent to the system logs

* Thu Aug 04 2011 David Zeuthen <davidz@redhat.com> 0.102-1
- Update to 0.102 release

* Fri May 13 2011 Bastien Nocera <bnocera@redhat.com> 0.101-7
- Allow setting the pretty hostname without a password for wheel,
  change matches systemd in git

* Mon May  2 2011 Matthias Clasen <mclasen@redhat.com> - 0.101-6
- Update the action id of the datetime mechanism

* Tue Apr 19 2011 David Zeuthen <davidz@redhat.com> - 0.101-5
- CVE-2011-1485 (#697951)

* Tue Mar 22 2011 Kevin Kofler <Kevin@tigcc.ticalc.org> - 0.101-4
- Also allow org.kde.kcontrol.kcmclock.save without password for wheel

* Thu Mar 17 2011 David Zeuthen <davidz@redhat.com> - 0.101-3
- Fix typo in pkla file (thanks notting)

* Thu Mar 17 2011 David Zeuthen <davidz@redhat.com> - 0.101-2
- Nuke desktop_admin_r and desktop_user_r groups - just use the
  wheel group instead (#688363)
- Update the set of configuration directives that gives users
  in the wheel group extra privileges

* Thu Mar 03 2011 David Zeuthen <davidz@redhat.com> - 0.101-1
- New upstream version

* Mon Feb 21 2011 David Zeuthen <davidz@redhat.com> - 0.100-1
- New upstream version

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.98-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jan 28 2011 Matthias Clasen <mclasen@redhat.com> - 0.98-6
- Own /usr/libexec/polkit-1

* Fri Nov 12 2010 Matthias Clasen <mclasen@redhat.com> - 0.98-5
- Enable introspection

* Thu Sep 02 2010 David Zeuthen <davidz@redhat.com> - 0.98-4
- Fix #629515 in a way that doesn't require autoreconf

* Thu Sep 02 2010 David Zeuthen <davidz@redhat.com> - 0.98-2
- Include polkitagentenumtypes.h (#629515)

* Mon Aug 23 2010 Matthias Clasen <mclasen@redhat.com> - 0.98-1
- Update to upstream release 0.98
- Co-own /usr/share/gtk-doc (#604410)

* Wed Aug 18 2010 Matthias Clasen <mclasen@redhat.com> - 0.97-5
- Rebuid to work around bodhi limitations

* Wed Aug 18 2010 Matthias Clasen <mclasen@redhat.com> - 0.97-4
- Fix a ConsoleKit interaction bug

* Fri Aug 13 2010 David Zeuthen <davidz@redhat.com> - 0.97-3
- Add a patch to make pkcheck(1) work the way libvirtd uses it (#623257)
- Require GLib >= 2.25.12 instead of 2.25.11
- Ensure polkit-gnome packages earlier than 0.97 are not used with
  these packages

* Mon Aug 09 2010 David Zeuthen <davidz@redhat.com> - 0.97-2
- Rebuild

* Mon Aug 09 2010 David Zeuthen <davidz@redhat.com> - 0.97-1
- Update to 0.97. This release contains a port from EggDBus to the
  GDBus code available in recent GLib releases.

* Fri Jan 15 2010 David Zeuthen <davidz@redhat.com> - 0.96-1
- Update to 0.96
- Disable introspection support for the time being

* Fri Nov 13 2009 David Zeuthen <davidz@redhat.com> - 0.95-2
- Rebuild

* Fri Nov 13 2009 David Zeuthen <davidz@redhat.com> - 0.95-1
- Update to 0.95
- Drop upstreamed patches

* Tue Oct 20 2009 Matthias Clasen <mclasen@redhat.com> - 0.95-0.git20090913.3
- Fix a typo in pklocalauthority(8)

* Mon Sep 14 2009 David Zeuthen <davidz@redhat.com> - 0.95-0.git20090913.2
- Refine how Obsolete: is used and also add Provides: (thanks Jesse
  Keating and nim-nim)

* Mon Sep 14 2009 David Zeuthen <davidz@redhat.com> - 0.95-0.git20090913.1
- Add bugfix for polkit_unix_process_new_full() (thanks Bastien Nocera)
- Obsolete old PolicyKit packages

* Sun Sep 13 2009 David Zeuthen <davidz@redhat.com> - 0.95-0.git20090913
- Update to git snapshot
- Drop upstreamed patches
- Turn on GObject introspection
- Don't delete desktop_admin_r and desktop_user_r groups when
  uninstalling polkit-desktop-policy

* Fri Sep 11 2009 David Zeuthen <davidz@redhat.com> - 0.94-4
- Add some patches from git master
- Sort pkaction(1) output
- Bug 23867 – UnixProcess vs. SystemBusName aliasing

* Thu Aug 13 2009 David Zeuthen <davidz@redhat.com> - 0.94-3
- Add desktop_admin_r and desktop_user_r groups along with a first cut
  of default authorizations for users in these groups.

* Wed Aug 12 2009 David Zeuthen <davidz@redhat.com> - 0.94-2
- Disable GObject Introspection for now as it breaks the build

* Wed Aug 12 2009 David Zeuthen <davidz@redhat.com> - 0.94-1
- Update to upstream release 0.94

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.93-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jul 20 2009 David Zeuthen <davidz@redhat.com> - 0.93-2
- Rebuild

* Mon Jul 20 2009 David Zeuthen <davidz@redhat.com> - 0.93-1
- Update to 0.93

* Tue Jun 09 2009 David Zeuthen <davidz@redhat.com> - 0.92-3
- Don't make docs noarch (I *heart* multilib)
- Change license to LGPLv2+

* Mon Jun 08 2009 David Zeuthen <davidz@redhat.com> - 0.92-2
- Rebuild

* Mon Jun 08 2009 David Zeuthen <davidz@redhat.com> - 0.92-1
- Update to 0.92 release

* Wed May 27 2009 David Zeuthen <davidz@redhat.com> - 0.92-0.git20090527
- Update to 0.92 snapshot

* Mon Feb  9 2009 David Zeuthen <davidz@redhat.com> - 0.91-1
- Initial spec file.
