/**
 * 异常类
 */

export class InkPathError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InkPathError';
  }
}

export class APIError extends InkPathError {
  code: string;
  statusCode: number;

  constructor(message: string, code: string = 'API_ERROR', statusCode: number = 0) {
    super(`[${code}] ${message}`);
    this.name = 'APIError';
    this.code = code;
    this.statusCode = statusCode;
  }
}

export class ValidationError extends InkPathError {
  code: string;

  constructor(message: string, code: string = 'VALIDATION_ERROR') {
    super(`[${code}] ${message}`);
    this.name = 'ValidationError';
    this.code = code;
  }
}
