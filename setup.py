#!/usr/bin/env python3
from setuptools import setup
from os import walk, path, environ

URL = "https://github.com/OpenVoiceOS/ovos-personal"
SKILL_CLAZZ = "PersonaSkill"
PYPI_NAME = "ovos-persona"

# below derived from github url to ensure standard skill_id
SKILL_AUTHOR, SKILL_NAME = URL.split(".com/")[-1].split("/")
SKILL_PKG = SKILL_NAME.lower().replace("-", "_")
PLUGIN_ENTRY_POINT = (
    f"{SKILL_NAME.lower()}.{SKILL_AUTHOR.lower()}={SKILL_PKG}:{SKILL_CLAZZ}"
)
PLUGIN_ENTRY_POINT = "persona.openvoiceos=ovos_persona.skill:PersonaSkill"

BASEDIR = path.abspath(path.dirname(__file__))


def get_version():
    """Find the version of the package"""
    version = None
    version_file = os.path.join(BASEDIR, "version.py")
    major, minor, build, alpha = (None, None, None, None)
    with open(version_file) as f:
        for line in f:
            if "VERSION_MAJOR" in line:
                major = line.split("=")[1].strip()
            elif "VERSION_MINOR" in line:
                minor = line.split("=")[1].strip()
            elif "VERSION_BUILD" in line:
                build = line.split("=")[1].strip()
            elif "VERSION_ALPHA" in line:
                alpha = line.split("=")[1].strip()

            if (major and minor and build and alpha) or "# END_VERSION_BLOCK" in line:
                break
    version = f"{major}.{minor}.{build}"
    if alpha and int(alpha) > 0:
        version += f"a{alpha}"
    return version


def get_requirements(requirements_filename: str):
    requirements_file = path.join(BASEDIR, requirements_filename)
    with open(requirements_file, "r", encoding="utf-8") as r:
        requirements = r.readlines()
    requirements = [
        r.strip() for r in requirements if r.strip() and not r.strip().startswith("#")
    ]
    if "MYCROFT_LOOSE_REQUIREMENTS" in environ:
        print("USING LOOSE REQUIREMENTS!")
        requirements = [r.replace("==", ">=").replace("~=", ">=") for r in requirements]
    return requirements


def find_resource_files():
    resource_base_dirs = ("locale", "ui", "vocab", "dialog", "regex", "weather_helpers")
    package_data = ["*.json"]
    for res in resource_base_dirs:
        if path.isdir(path.join(BASEDIR, res)):
            for directory, _, files in walk(path.join(BASEDIR, res)):
                if files:
                    package_data.append(
                        path.join(directory.replace(BASEDIR, "").lstrip("/"), "*")
                    )
    return package_data


with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name=PYPI_NAME,
    version=get_version(),
    description="persona ovos",
    url=URL,
    author="jarbasai",
    author_email="jarbasai@mailfence.com",
    license="MIT",
    package_dir={"ovos_persona": ""},
    package_data={"ovos_persona": find_resource_files()},
    packages=["ovos_persona"],
    zip_safe=True,
    install_requires=get_requirements("requirements.txt"),
    long_description="ovos persona",
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="ovos skill plugin persona",
    entry_points={"ovos.plugin.skill": PLUGIN_ENTRY_POINT},
)
