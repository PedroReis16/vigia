export interface UserProfileDto {
  id: string;
  name: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  pictureUrl?: string | null;
  canDeleteAccount?: boolean;
}
