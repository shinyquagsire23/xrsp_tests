@0xc38e084d4e4d5624;

struct HeadsetLens
{
    info8Unk1p0 @0 :Float32;
    info8Unk1p1 @1 :Float32;
    info8Unk2p0 @2 :Float32;
    info8Unk2p1 @3 :Float32;

    info8Unk3p0 @4 :Float32;
    info8Unk3p1 @5 :Float32;
    info8Unk4p0 @6 :Float32;
    info8Unk4p1 @7 :Float32;

    info8Unk5p0 @8 :Float32;
    info8Unk5p1 @9 :Float32;
    info8Unk6p0 @10 :Float32;
    info8Unk6p1 @11 :Float32;
}

struct HeadsetInfo7
{
    info7Unk1p0 @0 :UInt32;
    info7Unk1p1 @1 :UInt32;
}

struct HeadsetInfo6
{
    info6Unk1p0 @0 :UInt32;
    info6Unk1p1 @1 :UInt32;
}

struct HeadsetInfo5
{
    info5Unk1p0 @0 :Float32;
    info5Unk1p1 @1 :Float32;

    info5Unk2p0 @2 :Float32;
    info5Unk2p1 @3 :Float32;
}

struct HeadsetTimings
{
    frameRate @0 :UInt32;
    unused @1 :UInt32;

    timingsUnk2 @2 :HeadsetInfo5;
    timingsUnk3 @3 :HeadsetInfo6;
}

struct RectilinearDistortionParameters
{
    distortUnk1p0 @0 :Float32;
    distortUnk1p1 @1 :Float32;

    distortUnk2p0 @2 :Float32;
    distortUnk2p1 @3 :Float32;

    distortUnk3p0 @4 :Float32;
    distortUnk3p1 @5 :Float32;
}

struct AxisAlignedDistortionParameters
{
    distortUnk1p0 @0 :UInt32;
    distortUnk1p1 @1 :UInt32;

    distortUnk2p0 @2 :UInt32;
    distortUnk2p1 @3 :UInt32;

    distortUnk3p0 @4 :UInt32;
    distortUnk3p1 @5 :UInt32;
}

struct HeadsetDescription
{
    deviceType @0 :UInt32; # 1 == Quest 1, 2 == Quest 2, 3 == Quest 3

    resolutionWidth @1 :UInt32;
    resolutionHeight @2 :UInt32;
    refreshRateHz @3 :Float32;

    info2Unk3p0 @4 :Float32;
    info2Unk3p1 @5 :Float32;

    info2Unk4p0 @6 :Float32;
    info2Unk4p1 @7 :Float32;

    info2Unk5p0 @8 :Float32;
    info2Unk5p1 @9 :Float32;

    renderWidth @10 :UInt32;
    renderHeight @11 :UInt32;

    info2Unk7p0 @12 :UInt32;
    info2Unk7p1 @13 :UInt32;

    name @14 :Text;
    manufacturer @15 :Text;
    info2Unk10 @16 :HeadsetInfo7;
    leftLens @17 :HeadsetLens;
    rightLens @18 :HeadsetLens;
    timings @19 :List(HeadsetTimings);
}

struct HeadsetConfig
{
    description @0 :HeadsetDescription;
    kNative @1 :List(Float32);
    kAgressive @2 :List(Float32);
    rectilinearDistortionParameters @3 :RectilinearDistortionParameters;
    balancedAxisAlignedDistortionParameters @4 :AxisAlignedDistortionParameters;
    qualityAxisAlignedDistortionParameters @5 :AxisAlignedDistortionParameters;
    performanceAxisAlignedDistortionParameters @6 :AxisAlignedDistortionParameters;
}

struct PayloadHostInfo {
    payloadUnk1p0 @0 :UInt32;
    payloadUnk1p1 @1 :UInt32;

    payloadUnk2p0 @2 :UInt32;
    payloadUnk2p1 @3 :UInt32;

    payloadUnk3p0 @4 :UInt32;
    payloadUnk3p1 @5 :UInt32;

    payloadUnk4p0 @6 :UInt32;
    payloadUnk4p1 @7 :UInt32;

    payloadUnk5p0 @8 :UInt32;
    payloadUnk5p1 @9 :UInt32;

    serial @10 :Text;
    someGUID @11 :Text;
    unk6 @12 :Text;
    config @13 :HeadsetConfig;

    unk7 @14 :List(UInt32);
    softwareVersion @15 :Text;
    unk9 @16 :List(UInt16);
    unk10 @17 :List(UInt8);
}