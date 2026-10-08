export enum ClipStatus {
  Receiving = 'Receiving',
  Assembling = 'Assembling',
  Ready = 'Ready',
  Failed = 'Failed',
}

const CLIP_STATUS_VALUES = new Set<string>(Object.values(ClipStatus));

export function parseClipStatus(value: string | null | undefined): ClipStatus | null {
  if (!value || !CLIP_STATUS_VALUES.has(value)) {
    return null;
  }
  return value as ClipStatus;
}
