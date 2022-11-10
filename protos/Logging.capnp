@0xecf5a225496ec29b;
struct LogEntry {
  unk0 @0 :UInt64;
  timestampUs @1 :UInt64;
  data @2 :Text;
}

struct PayloadLogging {
  error @0 :List(LogEntry);
  warn @1 :List(LogEntry);
  debug @2 :List(LogEntry);
  info @3 :List(LogEntry);
}