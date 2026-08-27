enum ErrorCodes {
  unknownError(0),
  emailAlreadyInUse(7),
  fiwareCommandFailed(35),
  fiwareProvisionFailed(36);

  final int value;

  const ErrorCodes(this.value);
}
