%global cachedir %{_localstatedir}/cache/ddns-update
%global rundir   %{_localstatedir}/run/ddns-update
# This macro only defined by default around Fedora 18 time
%{!?_tmpfilesdir:%global _tmpfilesdir %{_prefix}/lib/tmpfiles.d}

Summary:           Client to update dynamic DNS host entries
Name:              ddns-update
Version:           0.1
Release:           1%{?dist}
License:           GPLv2+
Group:             System Environment/Daemons
URL:               https://github.com/lfarkas/%{name}
Source0:           https://github.com/lfarkas/%{name}/releases/%{name}-%{version}.tar.bz2

BuildArch:         noarch

Requires(pre):     shadow-utils
%if 0%{?fedora} > 14 || 0%{?rhel} > 6
BuildRequires:     systemd
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd
%else
Requires(post):    /sbin/chkconfig
Requires(preun):   /sbin/service, /sbin/chkconfig
Requires(postun):  /sbin/service
%endif
BuildRoot:         %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
ddns-update is a shell client used to update dynamic DNS entries with nsupdate
Features include: Operating as a daemon, manual and automatic updates, static 
and dynamic updates, optimized updates and sending update status to syslog or logfile.

%prep
%setup -q


%build
#nothing to do


%install
install -D -p -m 755 %{name} $RPM_BUILD_ROOT%{_bindir}/%{name}
install -D -p -m 600 ddns-update.conf \
    $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/%{name}.conf
%if 0%{?fedora} > 14 || 0%{?rhel} > 6
install -D -p -m 644 %{name}.service \
	$RPM_BUILD_ROOT%{_unitdir}/%{name}.service
install -D -p -m 644 tmpfiles-ddns-update.conf \
	$RPM_BUILD_ROOT%{_tmpfilesdir}/%{name}.conf
install -D -p -m 755 ddns-update.NetworkManager.systemd \
	$RPM_BUILD_ROOT%{_sysconfdir}/NetworkManager/dispatcher.d/50-%{name}
mkdir -p $RPM_BUILD_ROOT%{rundir}
%else
install -D -p -m 755 %{name}.initscript $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/%{name}
install -D -p -m 755 ddns-update.NetworkManager.sysv \
	$RPM_BUILD_ROOT%{_sysconfdir}/NetworkManager/dispatcher.d/50-%{name}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/{run}/%{name}
%endif


%clean
rm -rf $RPM_BUILD_ROOT


%pre
getent group %{name} > /dev/null || %{_sbindir}/groupadd -r %{name}
getent passwd %{name} > /dev/null || %{_sbindir}/useradd -r -g %{name} -d / -s /sbin/nologin -c "Dynamic DNS Updater" %{name}
exit 0

%post
%if 0%{?fedora} > 14 || 0%{?rhel} > 6
%if 0%{?fedora} >= 18
  %systemd_post %{name}.service
%else
if [ $1 -eq 1 ]; then 
  # Package install, not upgrade
  /bin/systemctl daemon-reload > /dev/null 2>&1 || :
fi
%endif
%else
/sbin/chkconfig --add %{name}
%endif

%preun
%if 0%{?fedora} > 14 || 0%{?rhel} > 6
%if 0%{?fedora} >= 18
  %systemd_preun %{name}.service
%else
# Work around RHBZ #655116
if [ $1 -eq 0 ]; then
  # Package removal, not upgrade
  /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
  /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi
%endif
%else
if [ $1 -eq 0 ]; then
  /sbin/service %{name} stop > /dev/null 2>&1 || :
  /sbin/chkconfig --del %{name}
fi
%endif


%postun
%if 0%{?fedora} > 14 || 0%{?rhel} > 6
%if 0%{?fedora} >= 18
  %systemd_postun_with_restart %{name}.service
%else
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ]; then
  # Package upgrade, not uninstall
  /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%endif
%else
if [ $1 -ne 0 ]; then
  /sbin/service %{name} condrestart > /dev/null 2>&1 || :
fi
%endif



%files
%defattr(-,root,root,-)
%license LICENSE
%doc README* sample/*

%if 0%{?fedora} > 14 || 0%{?rhel} > 6
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf
%ghost %attr(0755,%{name},%{name}) %dir %{_localstatedir}/run/%{name}/
%else
%{_sysconfdir}/rc.d/init.d/%{name}
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/run/%{name}/
%endif
%if 0%{?fedora}%{?rhel} > 4
%{_sysconfdir}/NetworkManager/dispatcher.d/50-%{name}
%endif
%attr(600,%{name},%{name}) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%{_bindir}/%{name}

%ghost %attr(0755,%{name},%{name}) %dir %{rundir}


%changelog
* Sat Oct 29 2016 Levente Farkas <lfarkas@lfarkas.org> - 0.1-1
- initial release
