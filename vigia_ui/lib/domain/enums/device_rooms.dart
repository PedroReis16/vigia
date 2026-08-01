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
  static DeviceRooms? fromString(String value) {
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
