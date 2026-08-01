enum DeviceRooms {
  bedroom,
  livingRoom,
  kitchen,
  bathroom,
  office,
  garage,
  backyard,
  frontyard,
}

extension DeviceRoomsExtension on DeviceRooms {
  String toApiString() {
    return switch (this) {
      DeviceRooms.bedroom => 'Bedroom',
      DeviceRooms.livingRoom => 'LivingRoom',
      DeviceRooms.kitchen => 'Kitchen',
      DeviceRooms.bathroom => 'Bathroom',
      DeviceRooms.office => 'Office',
      DeviceRooms.garage => 'Garage',
      DeviceRooms.backyard => 'Backyard',
      DeviceRooms.frontyard => 'Frontyard',
    };
  }

  static DeviceRooms? fromString(String? value) {
    if (value == null) return null;

    switch (value) {
      case 'Bedroom':
        return DeviceRooms.bedroom;
      case 'LivingRoom':
        return DeviceRooms.livingRoom;
      case 'Kitchen':
        return DeviceRooms.kitchen;
      case 'Bathroom':
        return DeviceRooms.bathroom;
      case 'Office':
        return DeviceRooms.office;
      case 'Garage':
        return DeviceRooms.garage;
      case 'Backyard':
        return DeviceRooms.backyard;
      case 'Frontyard':
        return DeviceRooms.frontyard;
      default:
        return null;
    }
  }
}
