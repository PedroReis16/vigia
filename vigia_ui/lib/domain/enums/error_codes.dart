enum ErrorCodes {
  unknownError(0),
  emailAlreadyInUse(7),
  groupUserLimitReached(26),
  inviteInvalid(27),
  inviteExpired(28),
  fiwareCommandFailed(35),
  fiwareProvisionFailed(36),
  notGroupMember(41),
  notificationNotFound(42),
  refreshTokenRequired(43),
  keycloakLogoutRejected(44),
  keycloakClientRequired(45),
  invalidProfilePicture(46),
  profilePictureTooLarge(47),
  invalidProfileName(48),
  invalidProfilePhone(49),
  profileUpdateFailed(50),
  accountDeleteForbidden(51);

  final int value;

  const ErrorCodes(this.value);
}
