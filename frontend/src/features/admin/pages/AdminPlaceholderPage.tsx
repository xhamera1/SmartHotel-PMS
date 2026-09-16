import { Typography } from '@mui/material'

type PlaceholderProps = {
  title: string
  detail: string
}

export function AdminPlaceholderPage({ title, detail }: PlaceholderProps) {
  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        {title}
      </Typography>
      <Typography color="text.secondary">{detail}</Typography>
    </>
  )
}
