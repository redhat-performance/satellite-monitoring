Name:          satellite-monitoring
Version:       1.1
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
mkdir -p %{buildroot}/usr/%{name}
cp README.md %{buildroot}/usr/%{name}
cp LICENSE %{buildroot}/usr/%{name}
cp Monitoring.png %{buildroot}/usr/%{name}
cp -r adhoc-scripts %{buildroot}/usr/%{name}
cp -r ansible %{buildroot}/usr/%{name}
cp -r docs %{buildroot}/usr/%{name}
mkdir %{buildroot}/usr/%{name}/conf
cp conf/hosts.ini.sample %{buildroot}/usr/%{name}/conf
cp conf/satmon.yaml %{buildroot}/usr/%{name}/conf
popd


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/usr/%{name}


%changelog
* Fri Jun 2 2017 Jan Hutar <jhutar@redhat.com> 1.1-1
- Init
