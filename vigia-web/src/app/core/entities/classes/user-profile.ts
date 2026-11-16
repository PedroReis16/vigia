export class UserProfile {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly firstName: string,
    public readonly lastName: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly pictureUrl: string | null,
    public readonly canDeleteAccount: boolean,
  ) {}
}
