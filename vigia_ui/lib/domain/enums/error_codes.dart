enum ErrorCodes {
  unknownError(0),
  emailAlreadyInUse(7);

  final int value;

  const ErrorCodes(this.value);
}
