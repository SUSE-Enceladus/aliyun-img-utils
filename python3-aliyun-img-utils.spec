#
# spec file for package python3-aliyun-img-utils
#
# Copyright (c) 2021 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


Name:           python3-aliyun-img-utils
Version:        0.0.1
Release:        0
Summary:        Command line utility for handling images in the Aliyun Cloud
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
URL:            https://github.com/SUSE-Enceladus/aliyun-img-utils
Source:         https://files.pythonhosted.org/packages/source/a/aliyun-img-utils/aliyun-img-utils-%{version}.tar.gz
BuildRequires:  python3-PyYAML
BuildRequires:  python3-click
BuildRequires:  python3-click-man
BuildRequires:  python3-oss2
BuildRequires:  python3-pytest
BuildRequires:  python3-coverage
BuildRequires:  python3-pytest-cov
Requires:       python3-PyYAML
Requires:       python3-click
Requires:       python3-oss2

%description
aliyun_img_utils provides an api and command line 
utilities for handling images in the Aliyun Cloud.

%prep
%setup -q -n aliyun-img-utils-%{version}

%build
python3 setup.py build
mkdir -p man/man1
python3 setup.py --command-packages=click_man.commands man_pages --target man/man1

%install
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}
install -d -m 755 %{buildroot}/%{_mandir}/man1
install -m 644 man/man1/*.1 %{buildroot}/%{_mandir}/man1

install -d -m 755 %{buildroot}%{_prefix}

%post
%postun

%check
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8
python3 -m pytest --cov=aliyun_img_utils

%files
%defattr(-,root,root)
%license LICENSE
%doc CHANGES.md CONTRIBUTING.md README.md
%{_mandir}/man1/*
%{_bindir}/aliyun-img-utils
%{python3_sitelib}/*

%changelog
