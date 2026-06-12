import { ACCEPTED_TYPES, MAX_FILE_SIZE_BYTES } from "../constants";

export function validateFileType(file: File): { valid: boolean; message?: string } {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return { valid: false, message: "Only MP4 files are supported." };
  }
  return { valid: true };
}

export function validateFileSize(file: File): { valid: boolean; message?: string } {
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return { valid: false, message: `File must be smaller than ${MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB.` };
  }
  return { valid: true };
}
