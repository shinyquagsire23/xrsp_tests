# Topics
TOPIC_AUI4A_ADV = 0x0
TOPIC_HOSTINFO_ADV = 0x1
TOPIC_COMMAND = 0x2
TOPIC_POSE = 0x3
TOPIC_MESH = 0x4
TOPIC_VIDEO = 0x5
TOPIC_AUDIO = 0x6
TOPIC_HAPTIC = 0x7
TOPIC_HANDS = 0x8
TOPIC_SKELETON = 0x9
TOPIC_SLICE_0 = 0xA
TOPIC_SLICE_1 = 0xB
TOPIC_SLICE_2 = 0xC
TOPIC_SLICE_3 = 0xD
TOPIC_SLICE_4 = 0xE
TOPIC_SLICE_5 = 0xF
TOPIC_SLICE_6 = 0x10
TOPIC_SLICE_7 = 0x11
TOPIC_SLICE_8 = 0x12
TOPIC_SLICE_9 = 0x13
TOPIC_SLICE_10 = 0x14
TOPIC_SLICE_11 = 0x15
TOPIC_SLICE_12 = 0x16
TOPIC_SLICE_13 = 0x17
TOPIC_SLICE_14 = 0x18
TOPIC_SLICE_15 = 0x19
TOPIC_AUDIO_CONTROL = 0x1A
TOPIC_USER_SETTINGS_SYNC = 0x1B
TOPIC_INPUT_CONTROL = 0x1C
TOPIC_ASW = 0x1D
TOPIC_BODY = 0x1E
TOPIC_RUNTIME_IPC = 0x1F
TOPIC_CAMERA_STREAM = 0x20
TOPIC_LOGGING = 0x21
TOPIC_22 = 0x22
TOPIC_23 = 0x23

# TOPIC_HOSTINFO_ADV
BUILTIN_PAIRING_ACK = 0x0
BUILTIN_INVITE = 0x1
BUILTIN_OK = 0x2
BUILTIN_ACK = 0x3
BUILTIN_ERROR = 0x4
BUILTIN_BYE = 0x5
BUILTIN_ECHO = 0x6
BUILTIN_PAIRING = 0x7
BUILTIN_CODE_GENERATION = 0x9
BUILTIN_CODE_GENERATION_ACK = 0xA
BUILTIN_RESERVED = 0xF

# TOPIC_COMMAND
COMMAND_TERMINATE = 0x00
COMMAND_1 = 0x01
COMMAND_2 = 0x02
COMMAND_3 = 0x03
COMMAND_4 = 0x04
COMMAND_5 = 0x05
COMMAND_6 = 0x06
COMMAND_7 = 0x07
COMMAND_8 = 0x08
COMMAND_9 = 0x09
COMMAND_A = 0x0A
COMMAND_RESET_GUARDIAN = 0x0B
COMMAND_TOGGLE_CHEMX = 0x0C
COMMAND_ENABLE_CAMERA_STREAM = 0x0D
COMMAND_DISABLE_CAMERA_STREAM = 0x0E
COMMAND_TOGGLE_ASW = 0x0F
COMMAND_10 = 0x10
COMMAND_DROP_FRAMES_STATE = 0x11

# TOPIC_RUNTIME_IPC
RIPC_MSG_CONNECT_TO_REMOTE_SERVER = 0x1
RIPC_MSG_RPC = 0x2
RIPC_MSG_ENSURE_SERVICE_STARTED = 0x4

# BUILTIN_ECHO
ECHO_PING = 0
ECHO_PONG = 1

# Internal
STATE_SEGMENT_META = 0
STATE_SEGMENT_READ = 1
STATE_EXT_READ = 2

POSEDATA_0 = 0x0

XrspResultLut = [
    "success",
    "invalid argument",
    "invalid data",
    "invalid state",
    "buffer too small",
    "out of memory",
    "topic does not exist",
    "topic already exists",
    "topic is not writable",
    "topic is not readable",
    "no device",
    "invalid transport description",
    "transport closed",
    "I/O error",
    "timeout occurred",
    "packet lost",
    "incompatible packet version",
    "forced termination",
    "property does not exist",
    "no session active",
    "not implemented",
    "unknown error",
    "network host disconnected",
    "ssl memory allocation failed",
    "ssl set cipher list failed",
    "ssl failed to use the provided cert",
    "ssl failed to use the privided private ",
    "cert and key provided failed validation",
    "ssl failed to set read/write fds",
    "ssl handshake failed",
    "peer failed to provide cert",
    "invalid pairing code",
    "pairing refused",
    "pairing timed out",
    "pairing_invalid_cert"
]

XrspTopic = [
    "aui4a-adv",
    "hostinfo-adv",
    "Command",
    "Pose",
    "Mesh",
    "Video",
    "Audio",
    "Haptic",
    "Hands",
    "Skeleton",
    "Slice 0",
    "Slice 1",
    "Slice 2",
    "Slice 3",
    "Slice 4",
    "Slice 5",
    "Slice 6",
    "Slice 7",
    "Slice 8",
    "Slice 9",
    "Slice 10",
    "Slice 11",
    "Slice 12",
    "Slice 13",
    "Slice 14",
    "Slice 15",
    "AudioControl",
    "UserSettingsSync",
    "InputControl",
    "Asw",
    "Body",
    "RuntimeIPC",
    "CameraStream",
    "Logging",
]

def XrspBuiltinMessageType(idx):
    if idx == BUILTIN_PAIRING_ACK:
        return "PAIRING_ACK"
    elif idx == BUILTIN_INVITE:
        return "INVITE"
    elif idx == BUILTIN_OK:
        return "OK"
    elif idx == BUILTIN_ACK:
        return "ACK"
    elif idx == BUILTIN_ERROR:
        return "ERROR"
    elif idx == BUILTIN_BYE:
        return "BYE"
    elif idx == BUILTIN_ECHO:
        return "ECHO"
    elif idx == BUILTIN_PAIRING:
        return "PAIRING"
    elif idx == BUILTIN_CODE_GENERATION:
        return "CODE_GENERATION"
    elif idx == BUILTIN_CODE_GENERATION_ACK:
        return "CODE_GENERATION_ACK"
    elif idx == BUILTIN_RESERVED:
        return "RESERVED"
    else:
        return "unknown"