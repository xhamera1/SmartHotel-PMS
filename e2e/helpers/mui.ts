import type { Locator, Page } from '@playwright/test'

/** MUI TextField puts data-testid on the FormControl wrapper — target the input. */
export function muiInput(page: Page, testId: string): Locator {
  return page.getByTestId(testId).locator('input')
}
