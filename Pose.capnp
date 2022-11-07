@0x999fa2218acd6729;

struct PoseStruct0 {
    unk0p0 @0 :Float32;
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
    unkA @20 :UInt64;
}

struct PoseStruct1 {
    unk0 @0 :UInt64;
}

struct PoseStruct2 {
    unk0p0 @0 :UInt32;
    unk0p1 @1 :UInt32;
    unk1p0 @2 :UInt32;
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
    struct0 @14 :PoseStruct0;
    struct1 @15 :PoseStruct1;
}

struct PoseStruct3 {
    unk0p0 @0 :Float32;
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
    unkA @20 :UInt64;
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
    unkF @30 :UInt64;
    list1 @31 :List(PoseStruct2);
    struct2 @32 :PoseStruct3;
    struct3 @33 :PoseStruct4;
}