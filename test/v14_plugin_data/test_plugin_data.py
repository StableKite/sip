import subprocess
import sys
import sysconfig

import pytest


def test_native_class_plugin_data(tmp_path, request):
    if request.config.getoption('--sip-abi-version') != 14:
        pytest.skip('requires ABI 14')

    (tmp_path / 'pyproject.toml').write_text('''
[build-system]
requires = ["sip >= 6.17"]
build-backend = "sipbuild.api"

[project]
name = "plugin_data_probe"

[tool.sip.project]
abi-version = "14.0"
sip-files-dir = "sip"
''')
    (tmp_path / 'project.py').write_text(r'''
from sipbuild import Project
from sipbuild.plugin import Plugin


class MetadataPlugin(Plugin):
    sip_key = "probe"

    def sip_class_generate_impl(self, writer, spec, klass):
        if klass.unscoped_cpp_name == "Annotated":
            writer.write("static const int annotated_data = 42;\n")
            return "annotated_data"


class TestProject(Project):
    def __init__(self):
        super().__init__()
        self.install_plugin(MetadataPlugin())
''')
    sip_dir = tmp_path / 'sip'
    sip_dir.mkdir()
    (sip_dir / 'plugin_data_probe.sip').write_text('''
%Module(name=plugin_data_probe, gil_use="NotUsed")
%MinimumABIVersion "14.0"

%InitialisationCode
    static int probe_value = 23;
    static const sipSymbolSpec exported[] = {
        {"plugin_probe_value", &probe_value},
        {nullptr, nullptr}
    };
    sipExportSymbols(exported);
%End

%ModuleHeaderCode
class Annotated {};
class Plain {};
%End

class Annotated {};
class Plain {};

int attached_value();
%MethodCode
    const auto *item = static_cast<const int *>(sipTypePluginData(sipType_Annotated));
    sipRes = item ? *item : -1;
%End

bool has_unannotated_data();
%MethodCode
    sipRes = sipTypePluginData(sipType_Plain) != nullptr;
%End

bool resolves_module_state();
%MethodCode
    sipRes = sipGetModuleState() == sipMS;
%End

int resolve_export();
%MethodCode
    const auto *value = static_cast<const int *>(sipImportSymbol("plugin_probe_value"));
    sipRes = value ? *value : -1;
%End
''')
    subprocess.run([sys.executable, '-m', 'sipbuild.tools.build'],
            cwd=tmp_path, check=True, timeout=90)
    suffix = sysconfig.get_config_var('EXT_SUFFIX')
    implementation, = (tmp_path / 'build').rglob('plugin_data_probe' + suffix)
    subprocess.run([sys.executable, '-I', '-S', '-c', '''
import sys

sys.path.insert(0, sys.argv[1])
import plugin_data_probe

assert plugin_data_probe.attached_value() == 42
assert not plugin_data_probe.has_unannotated_data()
assert plugin_data_probe.resolves_module_state()
assert plugin_data_probe.resolve_export() == 23
''', str(implementation.parent)], check=True, timeout=20)
