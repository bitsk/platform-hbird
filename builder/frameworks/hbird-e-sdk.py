
from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()

FRAMEWORK_DIR = env.PioPlatform().get_package_dir("framework-hbird-e-sdk")
assert FRAMEWORK_DIR and isdir(FRAMEWORK_DIR)

env.SConscript("_bare.py", exports="env")

env.Append(
    CCFLAGS=[
        "-include", "sys/cdefs.h"
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "drivers"),
        join(FRAMEWORK_DIR, "include"),
        join(FRAMEWORK_DIR, "env"),
    ],

    LIBPATH=[
        join(FRAMEWORK_DIR, "env"),
    ]
)

#
# Target: Build Core Library
#

libs = [
    env.BuildLibrary(
        join("$BUILD_DIR", "sdk-libwrap"),
        join(FRAMEWORK_DIR, "stubs")),

    env.BuildLibrary(
        join("$BUILD_DIR", "sdk-driver"),
        join(FRAMEWORK_DIR, "drivers", "plic")),

    env.BuildLibrary(
        join("$BUILD_DIR", "sdk-env"),
        join(FRAMEWORK_DIR, "env"),
        src_filter=env.subst("+<start.S> +<entry.S> +<init.c>"))
]

env.Prepend(LIBS=libs)