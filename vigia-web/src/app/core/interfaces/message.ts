export interface Message {
  message: string;
  type: 'success' | 'info' | 'warn' | 'error' | 'secondary' | 'contrast' | null;
  duration?: number;
  links?: {
    label: string;
    url: string;
  }[];
}
