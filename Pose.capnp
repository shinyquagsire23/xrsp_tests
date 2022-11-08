@0x999fa2218acd6729;

# Same as it ever was
# (look at old OVR SDKs for a C struct)
struct OvrPoseF {
    
    angVelX @0 :Float32;
    angVelY @1 :Float32;
    angVelZ @2 :Float32;
    linVelX @3 :Float32;
    linVelY @4 :Float32;
    linVelZ @5 :Float32;
    angAccX @6 :Float32;
    angAccY @7 :Float32;
    angAccZ @8 :Float32;
    linAccX @9 :Float32;
    linAccY @10 :Float32;
    linAccZ @11 :Float32;

    quatX @12 :Float32;
    quatY @13 :Float32;
    quatZ @14 :Float32;
    quatW @15 :Float32;
    posX @16 :Float32;
    posY @17 :Float32;
    posZ @18 :Float32;

    pad0 @19 :UInt32;
    timestamp @20 :UInt64; # not a double I don't think...
}

struct PoseStruct1 {
    unk0 @0 :UInt64;
}

struct PoseTrackedController {
    unk0p0 @0 :UInt32;
    buttons @1 :UInt32;
    capacitance @2 :UInt32;
    triggerZ @3 :Float32;
    gripZ @4 :Float32;
    stickX @5 :Float32;
    stickY @6 :Float32;
    touchpadX @7 :Float32;
    touchpadY @8 :Float32;
    touchpadPressure @9 :Float32;
    unk5p0 @10 :Float32;
    triggerCovered @11 :Float32;
    cameraCovered @12 :Float32; # ??
    unk6p1 @13 :Float32;
    struct0 @14 :OvrPoseF;
    struct1 @15 :PoseStruct1;
}

struct PoseStruct4 {
    unk0 @0 :UInt64;
}

struct PayloadPose {
    unk0p0 @0 :UInt32;
    unk0p1 @1 :Float32;
    unk1p0 @2 :Float32;
    unk1p1 @3 :Float32;
    unk2p0 @4 :Float32;
    unk2p1 @5 :Float32;
    unk3p0 @6 :Float32;
    unk3p1 @7 :Float32;
    unk4p0 @8 :Float32;
    unk4p1 @9 :Float32;
    unk5p0 @10 :Float32;
    unk5p1 @11 :Float32;
    unk6p0 @12 :Float32;
    unk6p1 @13 :Float32;
    unk7p0 @14 :Float32;
    unk7p1 @15 :Float32;
    unk8p0 @16 :Float32;
    unk8p1 @17 :Float32;
    unk9p0 @18 :Float32;
    unk9p1 @19 :Float32;
    unkAp0 @20 :Float32;
    unkAp1 @21 :Float32;
    unkBp0 @22 :Float32;
    unkBp1 @23 :Float32;
    unkCp0 @24 :Float32;
    unkCp1 @25 :Float32;
    unkDp0 @26 :Float32;
    unkDp1 @27 :Float32;
    unkEp0 @28 :Float32;
    unkEp1 @29 :Float32;
    timestamp @30 :UInt64;
    controllers @31 :List(PoseTrackedController);
    headset @32 :OvrPoseF;
    struct3 @33 :PoseStruct4;
}