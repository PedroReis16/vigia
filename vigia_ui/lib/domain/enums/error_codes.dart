enum ErrorCodes {
  unknownError(0),
  emailAlreadyInUse(7),
  fiwareCommandFailed(35),
  fiwareProvisionFailed(36),
  notGroupMember(41),
  notificationNotFound(42),
  refreshTokenRequired(43),
  keycloakLogoutRejected(44),
  keycloakClientRequired(45);

  final int value;

  const ErrorCodes(this.value);
}
