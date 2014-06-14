class Chunks:
    HEADER = 0x1
    TEXTURE = 0x2
    VERTICES = 0x3
    INDICES = 0x4
    CHILDREN = 0x9
    S_BONE_NAMES = 0xd
    S_IKDATA = 0x10
    S_USERDATA = 0x11
    S_DESC = 0x12
    S_MOTION_REFS_0 = 0x13


class ModelType:
    SKELETON_ANIM = 0x3
    SKELETON_GEOMDEF_ST = 0x5


class VertexFormat:
    FVF_1L = 0x12071980
    FVF_2L = 0x240e3300