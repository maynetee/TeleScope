export const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max)

export const formatCompactNumber = (value: number, locale: string = 'fr-FR') =>
  new Intl.NumberFormat(locale, { notation: 'compact' }).format(value)

export const formatDateTime = (
  value: string | number | Date,
  locale: string = 'fr-FR',
  options: Intl.DateTimeFormatOptions = { dateStyle: 'medium', timeStyle: 'short' },
) => new Intl.DateTimeFormat(locale, options).format(new Date(value))
