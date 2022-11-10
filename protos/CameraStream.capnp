@0x97ef77344d08d1b2;
struct CameraMetadata {
  width @0 :UInt32;
  height @1 :UInt32;
  metaUnk1p0 @2 :UInt16; # small ir: 1, big ir: 1, color: 3, float: 4
  metaUnk1p1 @3 :UInt16; # small ir: 2, big ir: 2, color: 3, float: 4
  metaUnk1p2 @4 :UInt16; # small ir: 1, big ir: 1, color: 3, float: 1
  metaUnk1p3 @5 :UInt16; # small ir: 0, big ir: 0, color: 0, float: 0
  metaUnk2p0 @6 :UInt32; # small ir: 1, big ir: 1, color: 3, float: 4

  stride @7 :UInt32; # in bytes
  bufferSize @8 :UInt32; # in bytes
  id @9 :Int32; # small ir: 1/2, big ir: 0/1, color: 4, float: -1
}

struct CameraData {
  dataUnk0 @0 :UInt64;
  data @1 :List(UInt8);
}

struct CameraStruct2 {
  struct2Unk0p0 @0 :UInt32;
  struct2Unk0p1 @1 :UInt32;
  metas @2 :List(CameraMetadata);
}

struct CameraStruct1 {
  struct1Unk0 @0 :UInt64; # small ir: 2, float: 1
  timestampSecs @1 :Float64;
  struct1Unk2 @2 :UInt64;
  struct1Unk3 @3 :CameraStruct2;
  struct1Unk4 @4 :List(CameraData);
}

struct PayloadCameraStream {
  unk0 @0 :UInt64;
  unk1 @1 :CameraStruct1;
}

struct CameraMetaData {
  dataUnk0 @0 :UInt64;
  data @1 :List(UInt8);
}

struct PayloadCameraStreamMeta {
  unk0 @0 :UInt64;
  metadata @1 :CameraMetaData;
}