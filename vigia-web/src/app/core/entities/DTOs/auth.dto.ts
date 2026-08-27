export interface AuthTokensDto {
  accessToken: string;
  refreshToken: string;
}

export interface LoginRequestDto {
  email: string;
  password: string;
}

export interface RegisterRequestDto {
  name: string;
  email: string;
  password: string;
}

export interface RefreshTokenRequestDto {
  refreshToken: string;
}

export interface ApiErrorDto {
  statusCode?: number;
  errorMessage?: string;
  errorCode?: string | number;
}
