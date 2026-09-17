/** PLN formatting — always from API numeric amounts, never reconstructed. */
const pln = new Intl.NumberFormat('pl-PL', {
  style: 'currency',
  currency: 'PLN',
})

export function formatPln(amount: number): string {
  return pln.format(amount)
}
