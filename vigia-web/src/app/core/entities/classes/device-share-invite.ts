export class DeviceShareInvite {
  constructor(
    public readonly token: string,
    public readonly inviteUrl: string,
    public readonly expiresAt: Date,
  ) {}
}
