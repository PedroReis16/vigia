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
      case 'BEDROOM':
        return DeviceRooms.bedroom;
      case 'LIVING_ROOM':
        return DeviceRooms.livingRoom;
      case 'KITCHEN':
        return DeviceRooms.kitchen;
      case 'BATHROOM':
        return DeviceRooms.bathroom;
      case 'OFFICE':
        return DeviceRooms.office;
      case 'GARAGE':
        return DeviceRooms.garage;
      case 'BACKYARD':
        return DeviceRooms.backyard;
      case 'FRONTYARD':
        return DeviceRooms.frontyard;
      default:
        return null;
    }
  }
}
