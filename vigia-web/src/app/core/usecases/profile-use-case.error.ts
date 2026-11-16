export class ProfileUseCaseError extends Error {
  constructor(readonly messageKey: string) {
    super(messageKey);
    this.name = 'ProfileUseCaseError';
  }
}
