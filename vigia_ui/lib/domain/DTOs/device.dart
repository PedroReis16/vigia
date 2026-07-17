import 'dart:typed_data';


class Device {
  final String id;
  final String description;
  final Uint8List? thumbnail;

  Device({required this.id, required this.description, this.thumbnail});
}
