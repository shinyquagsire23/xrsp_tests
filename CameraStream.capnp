@0x97ef77344d08d1b2;
struct CameraMetadata {
  metaUnk0 @0 :UInt64;
  metaUnk1 @1 :UInt64;
  metaUnk2 @2 :UInt64;
  metaUnk3 @3 :UInt64;
}

struct CameraData {
  dataUnk0 @0 :UInt64;
  data @1 :List(UInt8);
}

struct CameraStruct2 {
  struct2Unk0 @0 :UInt64;
  metas @1 :List(CameraMetadata);
}

struct CameraStruct1 {
  struct1Unk0 @0 :UInt64;
  struct1Unk1 @1 :UInt64;
  struct1Unk2 @2 :UInt64;
  struct1Unk3 @3 :CameraStruct2;
  struct1Unk4 @4 :List(CameraData);
}

struct PayloadCameraStream {
  unk0 @0 :UInt64;
  unk1 @1 :CameraStruct1;
}