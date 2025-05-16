#
# spec file for package python-aliyun-img-utils
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

%define upstream_name aliyun-img-utils
%if 0%{?suse_version} >= 1600
%define pythons %{primary_python}
%else
%{?sle15_python_module_pythons}
%endif
%global _sitelibdir %{%{pythons}_sitelib}

Name:           python-aliyun-img-utils
Version:        2.2.0
Release:        0
Summary:        Command line utility for handling images in the Aliyun Cloud
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
URL:            https://github.com/SUSE-Enceladus/aliyun-img-utils
Source:         https://files.pythonhosted.org/packages/source/a/aliyun-img-utils/aliyun-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  fdupes
BuildRequires:  %{pythons}-PyYAML
BuildRequires:  %{pythons}-click
BuildRequires:  %{pythons}-click-man
BuildRequires:  %{pythons}-oss2
BuildRequires:  %{pythons}-aliyun-python-sdk-core
BuildRequires:  %{pythons}-aliyun-python-sdk-ecs
BuildRequires:  %{pythons}-python-dateutil
BuildRequires:  %{pythons}-pytest
BuildRequires:  %{pythons}-coverage
BuildRequires:  %{pythons}-pytest-cov
BuildRequires:  %{pythons}-pip
BuildRequires:  %{pythons}-setuptools
BuildRequires:  %{pythons}-wheel
Requires:       %{pythons}-PyYAML
Requires:       %{pythons}-click
Requires:       %{pythons}-oss2
Requires:       %{pythons}-aliyun-python-sdk-core
Requires:       %{pythons}-aliyun-python-sdk-ecs
Requires:       %{pythons}-python-dateutil

Provides:       python3-aliyun-img-utils = %{version}
Obsoletes:      python3-aliyun-img-utils < %{version}

%description
aliyun_img_utils provides an api and command line 
utilities for handling images in the Aliyun Cloud.

%prep
%autosetup -n aliyun-img-utils-%{version}

%build
%pyproject_wheel
mkdir -p man/man1
%python_exec setup.py --command-packages=click_man.commands man_pages --target man/man1

%install
%pyproject_install
install -d -m 755 %{buildroot}/%{_mandir}/man1
install -m 644 man/man1/* %{buildroot}/%{_mandir}/man1
%fdupes %{buildroot}%{_sitelibdir}

%check
%pytest

%files
%license LICENSE
%doc CHANGES.md CONTRIBUTING.md README.md
%{_mandir}/man1/aliyun-img-utils-image-activate.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-create.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-delete.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-deprecate.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-info.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-publish.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-replicate.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-upload.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image-share-permission.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils-image.1%{?ext_man}
%{_mandir}/man1/aliyun-img-utils.1%{?ext_man}
%{_bindir}/aliyun-img-utils
%{_sitelibdir}/aliyun_img_utils/
%{_sitelibdir}/aliyun_img_utils-*.dist-info/

%changelog
