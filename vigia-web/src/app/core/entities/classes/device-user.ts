export class DeviceUser {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly userPictureUrl: string | null,
    public readonly isOwner: boolean,
  ) {}
}
