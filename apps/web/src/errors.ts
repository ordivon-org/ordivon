export class WebProblem extends Error {
  readonly status: number;
  readonly code: string;
  readonly title: string;

  constructor(status: number, code: string, title: string, detail: string) {
    super(detail);
    this.name = "WebProblem";
    this.status = status;
    this.code = code;
    this.title = title;
  }
}
