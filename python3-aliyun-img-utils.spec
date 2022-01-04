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

%{?!python_module:%define python_module() python-%{**} python3-%{**}}
%if 0%{?suse_version} >= 1500
%define skip_python2 1
%endif
Name:           python-aliyun-img-utils
Version:        1.8.0
Release:        0
Summary:        Command line utility for handling images in the Aliyun Cloud
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
URL:            https://github.com/SUSE-Enceladus/aliyun-img-utils
Source:         https://files.pythonhosted.org/packages/source/a/aliyun-img-utils/aliyun-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module PyYAML}
BuildRequires:  %{python_module click}
BuildRequires:  %{python_module click-man}
BuildRequires:  %{python_module oss2}
BuildRequires:  %{python_module aliyun-python-sdk-core}
BuildRequires:  %{python_module aliyun-python-sdk-ecs}
BuildRequires:  %{python_module python-dateutil}
BuildRequires:  %{python_module pytest}
BuildRequires:  %{python_module coverage}
BuildRequires:  %{python_module pytest-cov}
Requires:       python-PyYAML
Requires:       python-click
Requires:       python-oss2
Requires:       python-aliyun-python-sdk-core
Requires:       python-aliyun-python-sdk-ecs
Requires:       python-python-dateutil
Requires(post):   update-alternatives
Requires(postun):  update-alternatives

%python_subpackages

%description
aliyun_img_utils provides an api and command line 
utilities for handling images in the Aliyun Cloud.

%prep
%setup -q -n aliyun-img-utils-%{version}

%build
%python_build
mkdir -p man/man1
%python_exec setup.py --command-packages=click_man.commands man_pages --target man/man1

%install
%python_install
for i in man/man1/*.1 ; do
    install -p -D -m 644 $i %{buildroot}%{_mandir}/man1/$(basename $i)
done
%python_clone -a %{buildroot}%{_bindir}/aliyun-img-utils
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-activate.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-create.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-delete.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-deprecate.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-info.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-publish.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-replicate.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image-upload.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils-image.1
%python_clone -a %{buildroot}%{_mandir}/man1/aliyun-img-utils.1

%post
%{python_install_alternative aliyun-img-utils aliyun-img-utils-image-activate.1 aliyun-img-utils-image-create.1 aliyun-img-utils-image-delete.1 aliyun-img-utils-image-deprecate.1 aliyun-img-utils-image-info.1 aliyun-img-utils-image-publish.1 aliyun-img-utils-image-replicate.1 aliyun-img-utils-image-upload.1 aliyun-img-utils-image.1 aliyun-img-utils.1}

%postun
%python_uninstall_alternative aliyun-img-utils

%check
%pytest

%files %{python_files}
%license LICENSE
%doc CHANGES.md CONTRIBUTING.md README.md
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-activate.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-create.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-delete.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-deprecate.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-info.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-publish.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-replicate.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image-upload.1
%python_alternative %{_mandir}/man1/aliyun-img-utils-image.1
%python_alternative %{_mandir}/man1/aliyun-img-utils.1
%python_alternative %{_bindir}/aliyun-img-utils
%{python_sitelib}/*

%changelog
