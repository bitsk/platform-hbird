import sys
from os.path import join

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Default, DefaultEnvironment)


env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()

env.Replace(
    AR="riscv-none-embed-gcc-ar",
    AS="riscv-none-embed-as",
    CC="riscv-none-embed-gcc",
    GDB="riscv-none-embed-gdb",
    CXX="riscv-none-embed-g++",
    OBJCOPY="riscv-none-embed-objcopy",
    RANLIB="riscv-none-embed-gcc-ranlib",
    SIZETOOL="riscv-none-embed-size",

    ARFLAGS=["rcs"],

    SIZEPRINTCMD='$SIZETOOL -d $SOURCES',

    PROGSUFFIX=".elf"
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py", exports="env")

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
else:
    target_elf = env.BuildProgram()

AlwaysBuild(env.Alias("nobuild", target_elf))
target_buildprog = env.Alias("buildprog", target_elf, target_elf)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default .bin file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board_config.get("debug.tools", {})
upload_actions = []

if upload_protocol in debug_tools:
    openocd_args = [
        "-c",
        "debug_level %d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1),
        "-s", platform.get_package_dir("tool-openocd-hbird") or ""
    ]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", []))
    openocd_args.extend([
        "-c", "flash protect 0 0 last off; program {$SOURCE} %s verify; shutdown;" %
        board_config.get("upload").get("flash_start", "")
    ])
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS")
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

AlwaysBuild(env.Alias("upload", target_elf, upload_actions))


#
# Setup default targets
#

Default([target_buildprog, target_size])
