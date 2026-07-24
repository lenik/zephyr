declare module "node-gettext" {
  export default class Gettext {
    constructor(options?: { sourceLocale?: string; debug?: boolean });
    addTranslations(
      locale: string,
      domain: string,
      translations: object,
    ): void;
    setLocale(locale: string): void;
    setTextDomain(domain: string): void;
    gettext(msgid: string): string;
  }
}

declare module "gettext-parser" {
  export const mo: {
    parse(buffer: Buffer | Uint8Array): {
      charset: string;
      headers: Record<string, string>;
      translations: Record<string, unknown>;
    };
  };
  export const po: {
    parse(input: string | Buffer): {
      charset: string;
      headers: Record<string, string>;
      translations: Record<string, unknown>;
    };
  };
}
