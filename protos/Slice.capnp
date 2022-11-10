@0xf885ae51503e46e3;

struct PayloadQuat {
    x @0 :Float32;
    y @1 :Float32;
    z @2 :Float32;
    w @3 :Float32;
}

struct PayloadSlice {
  frameIdx @0 :UInt32;
  unk0p1 @1 :UInt32;
  unk1p0 @2 :UInt32;

  poseQuatX @3 :Float32;
  poseQuatY @4 :Float32;
  poseQuatZ @5 :Float32;
  poseQuatW @6 :Float32;
  poseX @7 :Float32;
  poseY @8 :Float32;
  poseZ @9 :Float32;

  timestamp05 @10 :UInt64;
  sliceNum @11 :UInt8;
  unk6p1 @12 :UInt8;
  unk6p2 @13 :UInt8;
  unk6p3 @14 :UInt8;
  blitYPos @15 :UInt32;
  unk7p0 @16 :UInt32;
  csdSize @17 :UInt32;
  videoSize @18 :UInt32;
  unk8p1 @19 :UInt32;

  timestamp09 @20 :UInt64;
  unkA @21 :UInt64; # some delta ns?
  timestamp0B @22 :UInt64;
  timestamp0C @23 :UInt64;
  timestamp0D @24 :UInt64;

  quat1 @25 :PayloadQuat;
  quat2 @26 :PayloadQuat;
}