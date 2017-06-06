Name:          satellite-monitoring
Version:       1.2
Release:       1%{?dist}
Summary:       Configure monitoring of Red Hat Satellite 6
License:       GPLv2
Group:         Development/Tools
URL:           https://github.com/redhat-performance/satellite-monitoring
Source0:       https://github.com/redhat-performance/satellite-monitoring/archive/%{name}-%{version}.tar.gz
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:     noarch
Requires:      ansible


%description
Configure monitoring of your Satellite and Capsules using Ansible playbooks


%prep
%setup -qc


%build


%install
rm -rf %{buildroot}
pushd %{name}-%{version}
rm -rf rel-eng
mkdir -p %{buildroot}/%{_datadir}/%{name}
cp README.md %{buildroot}/%{_datadir}/%{name}
cp LICENSE %{buildroot}/%{_datadir}/%{name}
cp Monitoring.png %{buildroot}/%{_datadir}/%{name}
cp -r adhoc-scripts %{buildroot}/%{_datadir}/%{name}
cp -r ansible %{buildroot}/%{_datadir}/%{name}
cp -r docs %{buildroot}/%{_datadir}/%{name}
mkdir %{buildroot}/%{_datadir}/%{name}/conf
cp conf/hosts.ini.sample %{buildroot}/%{_datadir}/%{name}/conf
cp conf/satmon.yaml %{buildroot}/%{_datadir}/%{name}/conf
popd


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/%{_datadir}/%{name}


%changelog
* Tue Jun 6 2017 Jan Hutar <jhutar@redhat.com> 1.2-1
- Install to /usr/share

* Fri Jun 2 2017 Jan Hutar <jhutar@redhat.com> 1.1-1
- Init
